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
import { Button } from "@/components/ui/button";


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
                    <ImageDisplay full_col url_base={`/api/query_image/${id}`} image_metrics={data.output_types['graph']}/>
                    <IndividualDisplay id={id} query_info={data}/>
                </div>
            </div>}
        </div>
    )
}


function IndividualDisplay({id, query_info} : {id: string, query_info: ResultInfo}) {
    const [queryNum, setQueryNum] = useState(0);
    const max_query = query_info.individual_count;

    return <div className="col-span-full my-2 space-y-3">
        <div className="flex space-x-3 justify-center">
        <div className="text-2xl">Individual Query : {queryNum} of {max_query-1}</div>
        <div className="space-x-2">
            <Button size={"sm"} onClick={() => setQueryNum((queryNum - 1 + max_query) % max_query)}>Previous</Button>
            <Button size={"sm"} onClick={() => setQueryNum((queryNum + 1) % max_query)}>Next</Button>
        </div>
        </div>
        <div className="grid-cols-2 grid">
        <ImageDisplay url_base={`/api/indv_query_image/${id}/${queryNum}`} image_metrics={query_info.individual_types['graph']}/>
        <JsonRender id={id} query_ind={queryNum}/>
        </div>
    </div>

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

function JsonRender({id, query_ind} : {id: string, query_ind: number}) {
    const { data, loading, error } = useFetch<any>(`/indv_query_json/${id}/${query_ind}`);
    return <>
        {loading && <div>Loading...</div>}
        {error && <div className="text-red-500 mt-2">{error}</div>}
        {data && data['IndividualQueryNodeExploration'] && <IndividualQueryNodeExploration data={data['IndividualQueryNodeExploration']}/>}
    </>
}

function IndividualQueryNodeExploration({ data }: { data: any }) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);
    const animationRef = useRef<NodeJS.Timeout | null>(null); // Store animation reference

    useEffect(() => {
        if (typeof window === "undefined" || !containerRef.current || !data) return;
        console.log("Graph Parsed...");

        if (sigmaInstance) {
            sigmaInstance.kill();
            setSigmaInstance(null);
        }

        const graph = new Graph();
        const g = new dagre.graphlib.Graph();
        g.setGraph({ rankdir: "TB", nodesep: 50, edgesep: 10, ranksep: 50 });
        g.setDefaultEdgeLabel(() => ({}));

        const bestKSet = new Set(data.best_k.map(String));
        const visitOrderSet = new Set(data.visit_order.map(String));
        const firstVisitedNode = data.visit_order[0].toString();
        const visitOrderMap = new Map();

        data.visit_order.forEach((node, index) => {
            visitOrderMap.set(node.toString(), index + 1);
        });

        Object.entries(data.parents).forEach(([child, parent]) => {
            const parentId = typeof parent === "string" || typeof parent === "number" ? parent.toString() : "";
            const childId = child.toString();

            if (!visitOrderSet.has(parentId) || !visitOrderSet.has(childId)) return;

            if (!graph.hasNode(parentId)) {
                let color = "#007bff";
                if (parentId === firstVisitedNode) color = "#a0a0a0";
                if (bestKSet.has(parentId)) color = "#ff0000";
                graph.addNode(parentId, { label: `(${visitOrderMap.get(parentId)}) ${parentId}`, size: 5, color });
                g.setNode(parentId, { width: 50, height: 50 });
            }

            if (!graph.hasNode(childId)) {
                let color = "#007bff";
                if (childId === firstVisitedNode) color = "#a0a0a0";
                if (bestKSet.has(childId)) color = "#ff0000";
                graph.addNode(childId, { label: `(${visitOrderMap.get(childId)}) ${childId}`, size: 5, color });
                g.setNode(childId, { width: 50, height: 50 });
            }

            if (!graph.hasEdge(parentId, childId)) {
                graph.addEdge(parentId, childId, { size: 1, color: "#aaa" });
                g.setEdge(parentId, childId);
            }
        });

        dagre.layout(g);

        g.nodes().forEach((nodeId) => {
            const { x, y } = g.node(nodeId);
            graph.setNodeAttribute(nodeId, "x", x);
            graph.setNodeAttribute(nodeId, "y", y);
        });

        const newSigmaInstance = new Sigma(graph, containerRef.current);
        setSigmaInstance(newSigmaInstance);

        // **Step 5️⃣: Animate Node Visit Order**
        let step = 0;
        const animateVisitOrder = () => {
            if (step >= data.visit_order.length) return;
            const nodeId = data.visit_order[step].toString();
            
            // Highlight visited node in green and increase size
            graph.setNodeAttribute(nodeId, "color", "#00ff00"); 
            graph.setNodeAttribute(nodeId, "size", 8);

            setTimeout(() => {
                // Revert back to original color and size after delay
                let originalColor = "#007bff";
                if (nodeId === firstVisitedNode) originalColor = "#a0a0a0";
                if (bestKSet.has(nodeId)) originalColor = "#ff0000";
                graph.setNodeAttribute(nodeId, "color", originalColor);
                graph.setNodeAttribute(nodeId, "size", 5);
                
                step++;
                animateVisitOrder(); // Recursively continue animation
            }, 100); // 600ms delay per step
        };

        animationRef.current = setTimeout(animateVisitOrder, 1000);

        return () => {
            newSigmaInstance.kill();
            if (animationRef.current) clearTimeout(animationRef.current);
        };
    }, [data]);

    return (
        <div className="p-3 min-h-[40vh] h-full">
            <div ref={containerRef} className="w-full rounded h-full bg-slate-100" />
        </div>
    );
}
