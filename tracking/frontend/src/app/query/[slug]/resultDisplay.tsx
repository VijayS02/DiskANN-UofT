'use client'

import useFetch from "@/util";
import { ResultInfo } from "../page";
import { useEffect, useRef, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  } from "@/components/ui/table"
  import dagre from "dagre";
import ImageDisplay from "@/app/imageDisplay";
import { Index } from "@/app/page";
import { IndexStatDisplay } from "@/app/index/[slug]/indexInfo";
import {
    Accordion,
    AccordionContent,
    AccordionItem,
    AccordionTrigger,
  } from "@/components/ui/accordion"


export default function ResultDisplay({id} : {id: string}) {
        const { data, loading, error } = useFetch< ResultInfo>(`/query_json/${id}`);
        console.log(data)
        return (
        <div>
            <div className="text-2xl mb-3">Results for Query: {id}</div>
            {loading && <div>Loading...</div>}
            {error && <div className="text-red-500 mt-2">{error}</div>}
            {data && <div>
                <div className="grid grid-cols-2 gap-4">
                    <StatDisplay res={data}/>
                    <ImageDisplay url_base={`/api/query_image/${id}`} image_metrics={data.output_types['graph']}/>
                    {/* {data.data?.BestKParentMetric && <BestKParentDisplay data={data.data.BestKParentMetric}/>} */}
                </div>
                
            </div>}
        </div>
    )
}


function StatDisplay({res} : {res: ResultInfo}) {
    const { data, loading, error } = useFetch<Record<string, { label: string }>>("/query_metrics");
    const { data: indexData } = useFetch< Index>(`/index_json/${res.index_name}`);

    const selectedMetrics = data ? res.metrics.map((key) => {
      return data[key]?.label;
    }) : res.metrics;

    
    return <>
        <div className="border border-gray-200 rounded col-span-full"><Table className="px-3">
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
      <TableRow>
        <TableCell className="font-medium">Metrics Tracked</TableCell>
        <TableCell className="text-right">
          <div className="justify-end flex divide-x-1">
            {selectedMetrics.length > 0 ? selectedMetrics.map((metric, i) => (
              <div key={i} className={i !== selectedMetrics.length -1 ? "px-3" : "pl-3"}>{metric}</div>
            )) : "None"}
          </div>
        </TableCell>
      </TableRow>
    </TableBody>
  </Table>
  </div>{indexData && <div className="col-span-full">
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1">
        <AccordionTrigger>
            <div className="text-2xl">
            Index Information : {res.index_name}
            </div>
        </AccordionTrigger>
        <AccordionContent>
            <IndexStatDisplay res={indexData}/>
        </AccordionContent>
      </AccordionItem>
    </Accordion>    
    </div>}</>
 
}



// function BestKParentDisplay({ data } : {data: Number[][][]}) {
//     const containerRef = useRef<HTMLDivElement | null>(null);
//     const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);

//     useEffect(() => {
//         if (typeof window === "undefined" || !containerRef.current || !data) return;
//         console.log("Graph Parsed...");

//         // **Clear previous graph before rendering a new one**
//         if (sigmaInstance) {
//             sigmaInstance.kill();
//             setSigmaInstance(null);
//         }

//         const graph = new Graph();
//         const nodeSet = new Set(); // Keep track of nodes
//         const endNodes = new Set(); // Track unique end nodes

//         // **Step 1️⃣: Process Paths and Create Nodes & Edges**
//         data.forEach((pathList) => {
//             pathList.forEach((path) => {
//                 if (path.length === 0) return;
//                 let prevNode: unknown = null;

//                 path.forEach((node, index) => {
//                     const nodeId = node.toString();

//                     // Add node if not exists
//                     if (!graph.hasNode(nodeId)) {
//                         let color = "#007bff"; // Default blue
//                         if (index === 0) color = "#28a745"; // Green for start node
//                         graph.addNode(nodeId, {
//                             label: `${nodeId}`,
//                             size: 5,
//                             color: color, // Default blue
//                             x: Math.random() * 1000,
//                             y: Math.random() * 1000,
//                         });
//                         nodeSet.add(nodeId);
//                     }

//                     // Track end nodes separately (last node in the path)
//                     if (index === path.length - 1) {
//                         endNodes.add(nodeId);
//                     }

//                     // Add edge from previous node (if exists)
//                     if (prevNode && !graph.hasEdge(prevNode, nodeId)) {
//                         graph.addEdge(prevNode, nodeId, { size: 1, color: "#aaa" });
//                     }

//                     prevNode = nodeId;
//                 });
//             });
//         });
//         endNodes.forEach((endNodeId) => {
//             graph.mergeNodeAttributes(endNodeId, {
//                 color: "#ff0000", // Cycle through colors
//                 size: 7, // Slightly bigger for visibility
//             });
//         });

//         // **Step 3️⃣: Use WebGL-Optimized Layout**
//         const layout = new FA2LayoutSupervisor(graph, {
//             settings: {
//                 barnesHutOptimize: true,
//                 scalingRatio: 4.0,
//                 gravity: 1.0,
//             },

//         });
//         layout.start();

//         // **Step 4️⃣: Render Graph with Sigma.js**
//         const newSigmaInstance = new Sigma(graph, containerRef.current);
//         setSigmaInstance(newSigmaInstance);

//         return () => {
//             layout.kill();
//             newSigmaInstance.kill();
//         };
//     }, [data]); // Runs when `data` updates

//     return <div className="p-3">
//         <div ref={containerRef} className="w-full rounded h-full bg-slate-100" />
//     </div>;
// }

function BestKParentDisplay({ data }: { data: Number[][][] }) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);

    useEffect(() => {
        if (typeof window === "undefined" || !containerRef.current || !data) return;
        console.log("Graph Parsed...");

        if (sigmaInstance) {
            sigmaInstance.kill();
            setSigmaInstance(null);
        }

        const graph = new Graph();
        const nodeSet = new Set();
        const endNodes = new Set();
        const g = new dagre.graphlib.Graph();
        g.setGraph({ rankdir: "TB", nodesep: 50, edgesep: 10, ranksep: 50 });
        g.setDefaultEdgeLabel(() => ({}));

        // **Step 1️⃣: Process Paths and Create Nodes & Edges**
        data.slice(0,1).forEach((pathList) => {
            pathList.forEach((path) => {
                if (path.length === 0) return;
                let prevNode: string | null = null;

                path.forEach((node, index) => {
                    const nodeId = node.toString();

                    if (!graph.hasNode(nodeId)) {
                        let color = "#007bff";
                        if (index === 0) color = "#28a745";
                        graph.addNode(nodeId, {
                            label: `${nodeId}`,
                            size: 5,
                            color: color,
                        });
                        nodeSet.add(nodeId);
                        g.setNode(nodeId, { width: 50, height: 50 });
                    }

                    if (index === path.length - 1) {
                        endNodes.add(nodeId);
                    }

                    if (prevNode && !graph.hasEdge(prevNode, nodeId)) {
                        graph.addEdge(prevNode, nodeId, { size: 1, color: "#aaa" });
                        g.setEdge(prevNode, nodeId);
                    }

                    prevNode = nodeId;
                });
            });
        });

        endNodes.forEach((endNodeId) => {
            graph.mergeNodeAttributes(endNodeId, {
                color: "#ff0000",
                size: 7,
            });
        });

        // **Step 3️⃣: Compute Layout using Dagre**
        dagre.layout(g);

        // Assign computed positions to graph nodes
        g.nodes().forEach((nodeId) => {
            const { x, y } = g.node(nodeId);
            graph.setNodeAttribute(nodeId, "x", x);
            graph.setNodeAttribute(nodeId, "y", y);
        });

        // **Step 4️⃣: Render Graph with Sigma.js**
        const newSigmaInstance = new Sigma(graph, containerRef.current);
        setSigmaInstance(newSigmaInstance);

        return () => {
            newSigmaInstance.kill();
        };
    }, [data]);

    return (
        <div className="p-3">
            <div ref={containerRef} className="w-full rounded h-full bg-slate-100" />
        </div>
    );
}
