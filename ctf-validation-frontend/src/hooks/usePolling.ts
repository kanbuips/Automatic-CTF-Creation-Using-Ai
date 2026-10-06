import { useCallback, useEffect, useRef, useState } from "react";
import { POLL_INTERVAL_MS } from "../utils/constants";
import { errorMessage } from "../utils/format";

/** Calls `fetcher` until `isDone(data)` is true. */
export function usePolling<T>(fetcher: () => Promise<T>, isDone: (d: T) => boolean, intervalMs = POLL_INTERVAL_MS) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fetcherRef = useRef(fetcher);
  const doneRef = useRef(isDone);
  fetcherRef.current = fetcher;
  doneRef.current = isDone;

  const refresh = useCallback(async () => {
    try {
      const d = await fetcherRef.current();
      setData(d);
      setError(null);
      return d;
    } catch (e) {
      setError(errorMessage(e));
      return null;
    }
  }, []);

  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      const d = await refresh();
      if (!stopped && !(d && doneRef.current(d))) timer = setTimeout(tick, intervalMs);
    };
    tick();
    return () => {
      stopped = true;
      clearTimeout(timer);
    };
  }, [refresh, intervalMs]);

  return { data, error, refresh };
}
