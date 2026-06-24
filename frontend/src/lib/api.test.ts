import { describe, it, expect, vi, afterEach } from "vitest";
import { ask } from "./api";

afterEach(() => vi.restoreAllMocks());

describe("ask", () => {
  it("POSTs the question and returns the parsed response", async () => {
    const fake = { answer: "ok", route: { route: "sql" }, citations: [], audit: [], limitations: [] };
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => fake });
    vi.stubGlobal("fetch", fetchMock);

    const result = await ask({
      question: "how many accidents",
      provider: "openai",
      model: "gpt-4o",
      apiKey: null,
      sessionId: "s1"
    });

    expect(result).toEqual(fake);
    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toMatch(/\/api\/ask$/);
    expect(init.method).toBe("POST");
    const body = JSON.parse(init.body);
    expect(body.question).toBe("how many accidents");
    expect(body.session_id).toBe("s1");
  });

  it("throws with the backend detail on error", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: "bad key" }) });
    vi.stubGlobal("fetch", fetchMock);
    await expect(
      ask({ question: "q", provider: "openai", model: "m", apiKey: "k", sessionId: "s" })
    ).rejects.toThrow("bad key");
  });
});
