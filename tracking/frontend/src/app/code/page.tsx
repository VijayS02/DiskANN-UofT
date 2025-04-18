"use client";

import { useState, useEffect } from "react";
import Editor from "@monaco-editor/react";
import { Button } from "@/components/ui/button";
import { io, Socket } from "socket.io-client";
import useFetch from "@/util";

export default function Page() {
  const [code, setCode] = useState("# Write your code here\n");
  const { data, loading, error, fetchData } = useFetch<any>("/exec", "POST");

  const handleRunCode = async () => {
    fetchData({ code });
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">
        Python Sandbox (Streaming Output)
      </h1>

      <div className="border-2 border-gray-300 rounded-md overflow-hidden">
        <Editor
          height="60vh"
          defaultLanguage="python"
          value={code}
          onChange={(val) => setCode(val || "")}
          theme="vs-dark"
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            wordWrap: "on",
          }}
        />
      </div>

      <div className="flex items-center gap-4">
        <Button size="sm" onClick={handleRunCode}>
          Run Code
        </Button>
      </div>
    </div>
  );
}
