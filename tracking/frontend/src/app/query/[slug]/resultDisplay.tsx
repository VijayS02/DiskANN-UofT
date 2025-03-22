'use client'

import useFetch from "@/util";
import { ResultInfo } from "../page";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import FA2LayoutSupervisor from "graphology-layout-forceatlas2/worker";
import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  } from "@/components/ui/table"

export default function ResultDisplay({id} : {id: string}) {
        const { data, loading, error } = useFetch< ResultInfo>(`/query_json/${id}`);
        console.log(data)
        return (
        <div>
            <div className="text-2xl mb-3">Results for Query: {id}</div>
            {loading && <div>Loading...</div>}
            {error && <div className="text-red-500 mt-2">{error}</div>}
            {data && <div>
                <div className="grid grid-cols-2 gap-2">
                    <div className="col-span-full">
                        <StatDisplay res={data}/>
                    </div>
                    <Image src={`/api/query_image/${id}`} className="w-full" alt="Query Image" width={500} height={500} />
                    {data.data.BestKParentMetric && <BestKParentDisplay data={data.data.BestKParentMetric}/>}
                </div>
                
            </div>}
        </div>
    )
}


function StatDisplay({res} : {res: ResultInfo}) {
    return <Table className="px-3">
    <TableCaption>Query settings.</TableCaption>
    <TableHeader>
      <TableRow>
        <TableHead className="w-[100px]">Parameter</TableHead>
        <TableHead className="text-right"></TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell className="font-medium">Index Name</TableCell>
        <TableCell className="text-right">{res.index_name}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">Query File</TableCell>
        <TableCell className="text-right">{res.query_file}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">K (In KNN)</TableCell>
        <TableCell className="text-right">{res.k}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">L Memory Scratch Size</TableCell>
        <TableCell className="text-right">{res.l}</TableCell>
      </TableRow>
    </TableBody>
  </Table>
 
}



function BestKParentDisplay({ data } : {data: Number[][][]}) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);

    useEffect(() => {
        if (typeof window === "undefined" || !containerRef.current || !data) return;
        console.log("Graph Parsed...");

        // **Clear previous graph before rendering a new one**
        if (sigmaInstance) {
            sigmaInstance.kill();
            setSigmaInstance(null);
        }

        const graph = new Graph();
        const nodeSet = new Set(); // Keep track of nodes
        const endNodes = new Set(); // Track unique end nodes

        // **Step 1️⃣: Process Paths and Create Nodes & Edges**
        data.forEach((pathList) => {
            pathList.forEach((path) => {
                if (path.length === 0) return;
                let prevNode: unknown = null;

                path.forEach((node, index) => {
                    const nodeId = node.toString();

                    // Add node if not exists
                    if (!graph.hasNode(nodeId)) {
                        graph.addNode(nodeId, {
                            label: `${nodeId}`,
                            size: 5,
                            color: "#007bff", // Default blue
                            x: Math.random() * 1000,
                            y: Math.random() * 1000,
                        });
                        nodeSet.add(nodeId);
                    }

                    // Track end nodes separately (last node in the path)
                    if (index === path.length - 1) {
                        endNodes.add(nodeId);
                    }

                    // Add edge from previous node (if exists)
                    if (prevNode && !graph.hasEdge(prevNode, nodeId)) {
                        graph.addEdge(prevNode, nodeId, { size: 1, color: "#aaa" });
                    }

                    prevNode = nodeId;
                });
            });
        });
        endNodes.forEach((endNodeId) => {
            graph.mergeNodeAttributes(endNodeId, {
                color: "#ff0000", // Cycle through colors
                size: 7, // Slightly bigger for visibility
            });
        });

        // **Step 3️⃣: Use WebGL-Optimized Layout**
        const layout = new FA2LayoutSupervisor(graph, {
            settings: { barnesHutOptimize: true },
        });
        layout.start();

        // **Step 4️⃣: Render Graph with Sigma.js**
        const newSigmaInstance = new Sigma(graph, containerRef.current);
        setSigmaInstance(newSigmaInstance);

        return () => {
            layout.kill();
            newSigmaInstance.kill();
        };
    }, [data]); // Runs when `data` updates

    return <div className="p-3">
        <div ref={containerRef} className="w-full rounded h-full bg-slate-100" />
    </div>;
}