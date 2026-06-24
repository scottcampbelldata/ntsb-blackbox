import { useEffect, useState } from "react";
import { fetchContext, type RelatedCoverage } from "./api";
import type { AskResponse } from "../types";

type Citation = AskResponse["citations"][number];

export type CoverageState = {
  byId: Record<string, RelatedCoverage>;
  loading: boolean;
};

function hasIdentifiers(c: Citation): boolean {
  return Boolean(c.make || c.model || c.city || c.state || c.event_year != null);
}

// Fetches news coverage for every citation that carries enough identifying
// fields to query GDELT, in parallel, as soon as an answer arrives. Citations
// with no make/model/city/state/year are skipped because the query would be
// useless. Results are keyed by NTSB number so both the top news panel and the
// inline citation list can read from one fetch.
export function useRelatedCoverage(citations: Citation[]): CoverageState {
  const [byId, setById] = useState<Record<string, RelatedCoverage>>({});
  const [loading, setLoading] = useState(false);

  const signature = citations.map((c) => c.ntsb_no).join("|");

  useEffect(() => {
    const targets = citations.filter(hasIdentifiers);
    setById({});
    if (targets.length === 0) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    setLoading(true);

    Promise.all(
      targets.map(async (c) => {
        try {
          const data = await fetchContext({
            make: c.make,
            model: c.model,
            city: c.city,
            state: c.state,
            year: c.event_year
          });
          return [c.ntsb_no, data] as const;
        } catch {
          return null;
        }
      })
    ).then((results) => {
      if (cancelled) return;
      const next: Record<string, RelatedCoverage> = {};
      for (const result of results) {
        if (result) next[result[0]] = result[1];
      }
      setById(next);
      setLoading(false);
    });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [signature]);

  return { byId, loading };
}
