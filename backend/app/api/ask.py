from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from backend.app.analytics.chart_planner import plan_chart
from backend.app.analytics.query_planner import QueryPlanningError, plan_sql
from backend.app.analytics.router import route_question
from backend.app.answer.audit import AuditTrail
from backend.app.answer.composer import default_limitations, summarize_table
from backend.app.data.db import QueryExecutionError, run_validated_query
from backend.app.llm.planner import generate_sql, synthesize_retrieval_answer
from backend.app.retrieval.service import retrieval_service
from providers import SessionKeyStore, redact_secrets


router = APIRouter(prefix="/api")
key_store = SessionKeyStore()


class AskRequest(BaseModel):
    question: str = Field(min_length=3)
    provider: Literal["openai", "anthropic", "gemini"] | None = None
    model: str | None = None
    api_key: str | None = Field(default=None, repr=False)
    chart_preference: Literal["auto", "chart", "table"] = "auto"
    session_id: str | None = None


class ClearKeyRequest(BaseModel):
    provider: Literal["openai", "anthropic", "gemini"] | None = None
    session_id: str | None = None


def _session_id(body_session_id, header_session_id):
    return body_session_id or header_session_id or str(uuid4())


@router.post("/keys/clear")
def clear_key(request: ClearKeyRequest, x_session_id: str | None = Header(default=None)):
    session_id = _session_id(request.session_id, x_session_id)
    if request.provider:
        key_store.clear_key(session_id, request.provider)
    else:
        key_store.clear_session(session_id)
    return {"ok": True, "session_id": session_id}


@router.post("/ask")
async def ask(request: AskRequest, x_session_id: str | None = Header(default=None)):
    session_id = _session_id(request.session_id, x_session_id)
    secrets = [request.api_key]
    audit = AuditTrail()
    question = request.question.strip()

    api_key = None
    if request.provider and request.api_key:
        key_store.set_key(session_id, request.provider, request.api_key)
        api_key = request.api_key
        audit.add("provider_key", f"Accepted {request.provider} key for this in-memory session.")
    elif request.provider and key_store.get_key(session_id, request.provider):
        api_key = key_store.get_key(session_id, request.provider)
        audit.add("provider_key", f"Using existing in-memory {request.provider} key for this session.")

    route = route_question(question)
    audit.add("route", f"Question routed to {route['route']}.")

    table = None
    sql = None
    chart_spec = None
    citations = []
    answer = None
    confidence = 0.65

    try:
        if route["route"] in ("sql", "chart", "both"):
            wants_chart = request.chart_preference != "table"
            candidate_sql = None
            title = None
            should_chart = False
            try:
                plan = plan_sql(question, wants_chart=wants_chart)
                candidate_sql = plan.sql
                title = plan.title
                confidence = plan.confidence
                should_chart = plan.chart
                audit.add("sql_plan", f"Selected deterministic plan: {plan.title}.")
            except QueryPlanningError:
                if not request.provider or not api_key:
                    route["route"] = "retrieval"
                    audit.add("sql_plan", "No deterministic SQL plan matched; falling back to narrative retrieval.")
                else:
                    candidate_sql = await generate_sql(
                        request.provider,
                        api_key=api_key,
                        model=request.model,
                        question=question,
                    )
                    title = "Model-Planned Analysis"
                    confidence = 0.62
                    should_chart = wants_chart
                    audit.add("sql_plan", "Generated candidate SQL with provider model.")

            if candidate_sql:
                result = run_validated_query(candidate_sql)
                audit.add("sql_guard", "SQL validated before execution.")
                audit.add("sql_execution", f"Executed query and returned {result.row_count} rows.")
                table = {"columns": result.columns, "rows": result.rows}
                sql = result.sql
                answer = summarize_table(question, result.rows, route["route"])

                if should_chart and result.columns and result.rows and request.chart_preference != "table":
                    chart_spec = plan_chart(question, result.columns, title=title)
                    if chart_spec:
                        audit.add("chart", "Generated and validated Vega-Lite chart spec.")

        if route["route"] in ("retrieval", "both"):
            citations = retrieval_service.search(question)
            audit.add("retrieval", f"Retrieved {len(citations)} cited accident reports with BM25.")
            if not answer:
                answer = (
                    "The strongest matching reports are listed as citations with matched passages and "
                    "probable-cause text. This is narrative retrieval, not a statistical count."
                )
            if request.provider and api_key and citations:
                answer = await synthesize_retrieval_answer(
                    request.provider,
                    api_key=api_key,
                    model=request.model,
                    question=question,
                    citations=citations,
                )
                audit.add("answer_synthesis", "Synthesized cited narrative answer with provider model.")

    except Exception as exc:
        message = redact_secrets(str(exc), secrets)
        raise HTTPException(status_code=400, detail=message) from exc

    return {
        "session_id": session_id,
        "question": question,
        "route": route,
        "answer": answer or "No answer path produced a result.",
        "sql": sql,
        "table": table,
        "chart_spec": chart_spec,
        "citations": citations,
        "confidence": confidence,
        "limitations": default_limitations(route["route"]),
        "audit": audit.to_list(),
    }
