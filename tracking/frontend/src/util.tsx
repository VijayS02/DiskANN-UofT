import { useState, useEffect, useCallback } from "react";
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
}

export function toSuperscript(num: { toString: () => string; }) {
    const superscripts = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', '5': '⁵', 
        '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    };
    return num.toString().split('').map(d => superscripts[d as keyof typeof superscripts] || d).join('');
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
            if (data === null) setLoading(true);
            setError(null);

            try {
                const requestOptions: RequestInit = { method };

                if (method === "POST") {
                    const bodyData = newPostData || postData;
                    if (bodyData instanceof FormData) {
                        requestOptions.body = bodyData; // Browser sets headers automatically
                    } else{
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
