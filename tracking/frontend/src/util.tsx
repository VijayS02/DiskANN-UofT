import { useState, useEffect, useCallback, useRef } from "react";
const msgpack = require("msgpack-lite");

type FetchMethod = "GET" | "POST";

interface FetchResult<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  fetchData: (postData?: unknown) => void; // Exposed function for manual fetching
}

interface FetchOptions {
  pollIntervalMs?: number; // Optional polling interval for GET requests
  onProgress?: (percent: number) => void;
}

export function toSuperscript(num: { toString: () => string }) {
  const superscripts = {
    "0": "⁰",
    "1": "¹",
    "2": "²",
    "3": "³",
    "4": "⁴",
    "5": "⁵",
    "6": "⁶",
    "7": "⁷",
    "8": "⁸",
    "9": "⁹",
  };
  return num
    .toString()
    .split("")
    .map((d) => superscripts[d as keyof typeof superscripts] || d)
    .join("");
}

// @ts-ignore: Prevent JSX parsing
const useFetch = <T,>(
  url: string,
  method: FetchMethod = "GET",
  initialPostData?: unknown,
  options: FetchOptions = {}
): FetchResult<T> => {
  const { pollIntervalMs } = options;
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [postData, setPostData] = useState<unknown | null>(initialPostData);

  // Store the latest data reference without causing re-renders
  const dataRef = useRef<T | null>(null);

  const fetchData = useCallback(
    async (newPostData?: unknown) => {
      if (dataRef.current === null) {
        console.log("No data!");
        setLoading(true);
      }
      setError(null);
      const bodyData = newPostData || postData;

      try {
        if (
          method === "POST" &&
          bodyData instanceof FormData &&
          options.onProgress
        ) {
          const xhr = new XMLHttpRequest();

          xhr.open("POST", "/api" + url);

          xhr.upload.onprogress = (event) => {
            console.log("XHR EVENT!", event);
            if (event.lengthComputable) {
              const percent = (event.loaded / event.total) * 100;
              if (options.onProgress) {
                options.onProgress(Math.round(percent));
              }
            }
          };

          xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
              try {
                const response = JSON.parse(xhr.responseText);
                dataRef.current = response;
                setData(response);
              } catch {
                dataRef.current = null;
                setData(null);
              }
            } else {
              setError(`Upload failed with status ${xhr.status}`);
            }
            setLoading(false);
          };

          xhr.onerror = () => {
            setError("Upload failed.");
            setLoading(false);
          };

          setPostData(bodyData);
          xhr.send(bodyData);
          return;
        }

        const requestOptions: RequestInit = { method };

        if (method === "POST") {
          const bodyData = newPostData || postData;
          if (bodyData instanceof FormData) {
            requestOptions.body = bodyData; // Browser sets headers automatically
          } else {
            requestOptions.headers = { "Content-Type": "application/json" };
            requestOptions.body = JSON.stringify(bodyData);
          }
          setPostData(bodyData); // Store latest post data
        }

        const response = await fetch("/api" + url, requestOptions);
        if (!response.ok) {
          throw new Error(`${response.status}`);
        }
        const contentType = response.headers.get("Content-Type");
        let result: T;

        if (contentType && contentType.includes("application/msgpack")) {
          const arrayBuffer = await response.arrayBuffer(); // Get binary data
          result = msgpack.decode(new Uint8Array(arrayBuffer)) as T; // Decode MessagePack
        } else {
          result = await response.json(); // Fallback to JSON if not MessagePack
        }

        // Compare with dataRef instead of state
        if (JSON.stringify(dataRef.current) !== JSON.stringify(result)) {
          dataRef.current = result;
          setData(result);
        }
        setLoading(false);
      } catch (err) {
        setError((err as Error).message);
        setLoading(false);
      }
    },
    [url, method, postData, options.onProgress]
  );

  useEffect(() => {
    let intervalId: NodeJS.Timeout | null = null;
    let isMounted = true;

    const initialFetch = async () => {
      if (method === "GET") {
        await fetchData(); // Auto-fetch for GET

        // Only set up polling after initial fetch completes
        if (pollIntervalMs && isMounted) {
          intervalId = setInterval(() => fetchData(), pollIntervalMs);
        }
      }
    };

    initialFetch();

    return () => {
      isMounted = false;
      if (intervalId) clearInterval(intervalId);
    };
  }, [url, method, fetchData, pollIntervalMs]);

  return { data, loading, error, fetchData };
};

export default useFetch;
