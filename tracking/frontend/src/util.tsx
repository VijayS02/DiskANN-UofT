import { useState, useEffect, useCallback } from "react";

type FetchMethod = "GET" | "POST";

interface FetchResult<T> {
    data: T | null;
    loading: boolean;
    error: string | null;
    fetchData: (postData?: unknown) => void; // Exposed function for manual fetching
}

interface FetchOptions {
    pollIntervalMs?: number; // Optional polling interval for GET requests
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

    const fetchData = useCallback(
        async (newPostData?: unknown) => {
            setLoading(true);
            setError(null);

            try {
                const requestOptions: RequestInit = { method };

                if (method === "POST") {
                    const bodyData = newPostData || postData;
                    requestOptions.headers = { "Content-Type": "application/json" };
                    requestOptions.body = JSON.stringify(bodyData);
                    setPostData(bodyData); // Store latest post data
                }

                const response = await fetch(url, requestOptions);
                if (!response.ok) {
                    throw new Error(`${response.status}`);
                }
                const result: T = await response.json();
                setData(result);
            } catch (err) {
                setError((err as Error).message);
            } finally {
                setLoading(false);
            }
        },
        [url, method, postData]
    );

    useEffect(() => {
        let intervalId: NodeJS.Timeout | null = null;
        let isMounted = true;

        if (method === "GET") {
            fetchData(); // Auto-fetch for GET
            if (pollIntervalMs) {
                intervalId = setInterval(() => fetchData(), pollIntervalMs);
            }
        }

        return () => {
            isMounted = false;
            if (intervalId) clearInterval(intervalId);
        };
    }, [url, method, fetchData, pollIntervalMs]);

    return { data, loading, error, fetchData };
};

export default useFetch;
