"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Editor from "@monaco-editor/react";
import { Button } from "@/components/ui/button";
import { io } from "socket.io-client";
import useFetch from "@/util";
import { GraphMap } from "@/components/msgpackRender";

import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function Page() {
  const [code, setCode] = useState("# Write your code here\n");
  const { fetchData } = useFetch<any>("/code/exec", "POST");

  const handleRunCode = useCallback(() => {
    fetchData({ code });
  }, [code, fetchData]);

  const terminalRef = useRef(null);
  const runRef = useRef(() => {});

  useEffect(() => {
    runRef.current = () => {
      fetchData({ code });
    };
  }, [code]);

  useEffect(() => {
    const socket = io("localhost:5000");

    const handleTerminalOutput = (data: { status: string }) => {
      if (!terminalRef.current) return;

      const newLog = document.createElement("p");
      newLog.innerText = data.status;
      if (data.status.startsWith("ERROR")) {
        newLog.classList.add("text-red-500");
      }
      terminalRef.current.appendChild(newLog);
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    };

    socket.on("terminal_output", handleTerminalOutput);
    return () => {
      socket.off("terminal_output", handleTerminalOutput);
      socket.disconnect();
    };
  }, []);

  return (
    <div className="space-y-3">
      <div className="flex justify-between">
        <h1 className="text-2xl font-semibold">Python Sandbox</h1>
        <Button size="sm" onClick={handleRunCode}>
          Run Code
        </Button>
      </div>

      <div className="border-2 border-gray-300 rounded-md overflow-hidden">
        <Editor
          height="60vh"
          defaultLanguage="python"
          value={code}
          onChange={(val) => setCode(val || "")}
          theme="vs-dark"
          onMount={(editor, monaco) => {
            editor.addCommand(
              monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter,
              () => runRef.current()
            );
          }}
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            wordWrap: "on",
          }}
        />

        <div className="bg-gray-900 text-white p-4 h-[20vh]">
          <div
            id="terminal"
            ref={terminalRef}
            className="h-full overflow-auto font-mono text-sm"
          ></div>
        </div>
      </div>

      <Graphs />
    </div>
  );
}

function Graphs() {
  const { data: graphList } = useFetch<string[]>("/code/list_graphs");
  const [selectedGraph, setSelectedGraph] = useState<string | null>(null);
  const [availableGraphs, setAvailableGraphs] = useState<string[]>([]);

  useEffect(() => {
    if (graphList) {
      setAvailableGraphs(graphList);
      if (!selectedGraph && graphList.length > 0) {
        setSelectedGraph(graphList[0]);
      }
    }
  }, [graphList]);

  useEffect(() => {
    const socket = io("localhost:5000");

    const handleNewGraph = (data: { filename: string }) => {
      setAvailableGraphs((prev) => {
        const updated = [...new Set([...prev, data.filename])];
        return updated;
      });
      setSelectedGraph(data.filename);
    };

    socket.on("new_graph", handleNewGraph);
    return () => {
      socket.off("new_graph", handleNewGraph);
      socket.disconnect();
    };
  }, []);

  if (!availableGraphs.length || !selectedGraph) return null;

  return (
    <div className="mt-2">
      <div className="text-xl">Graphs</div>
      <MultiGraphRenderer
        graphIds={availableGraphs}
        selectedGraph={selectedGraph}
        setSelectedGraph={setSelectedGraph}
      />
    </div>
  );
}

function MultiGraphRenderer({
  graphIds,
  selectedGraph,
  setSelectedGraph,
}: {
  graphIds: string[];
  selectedGraph: string;
  setSelectedGraph: (graphId: string) => void;
}) {
  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Interactive Graphs</CardTitle>
        <CardAction>
          <Select value={selectedGraph} onValueChange={setSelectedGraph}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select a graph" />
            </SelectTrigger>
            <SelectContent>
              {graphIds.map((graphId) => (
                <SelectItem key={graphId} value={graphId}>
                  {graphId}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent>
        {selectedGraph && <RenderGraph graphId={selectedGraph} />}
      </CardContent>
    </Card>
  );
}

function RenderGraph({ graphId }: { graphId: string }) {
  const { data } = useFetch<any>(`/code/graph/${graphId}`, "GET", undefined, {
    pollIntervalMs: 3000,
  });

  if (!data) return null;

  const metadata = data.meta;
  if (!metadata) return null;

  const graphType = metadata?.type as keyof typeof GraphMap;
  const GraphComponent = GraphMap[graphType];
  if (!GraphComponent) return null;

  const props = {
    title: metadata.props.title,
    xLabel: metadata.props.x,
    yLabel: metadata.props.y,
    yLog: metadata.props.ylog ?? false,
    data: data.data,
  };

  return (
    <div key={graphId}>
      <GraphComponent key={graphId} {...props} />
    </div>
  );
}
