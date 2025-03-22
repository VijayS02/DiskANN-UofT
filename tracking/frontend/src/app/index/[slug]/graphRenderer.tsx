'use client'
import Graph from "graphology";
import { useEffect, useRef, useState } from "react";
import Sigma from "sigma";
import FA2LayoutSupervisor from "graphology-layout-forceatlas2/worker";


const fetchAndParseCSV = async () => {
    try {
        const response = await fetch("/api/download");
        if (!response.ok) throw new Error("Failed to fetch");

        const text = await response.text(); // Read as text
        const rows = text.split("\n").map(row => row.split(",").map(Number)); // Convert to array
        rows.pop(); // Remove last empty row
        return rows;
    } catch (error) {
        console.error("Error fetching or parsing CSV:", error);
    }
};


function RenderGraph({data}) {
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [sigmaInstance, setSigmaInstance] = useState<Sigma | null>(null);

    useEffect(() => {
        if (typeof window === "undefined") return;
        if (!containerRef.current) return;

        if (!data) return;
        console.log("Graph Parsed...");

        // **Clear previous graph before rendering a new one**
        if (sigmaInstance) {
            sigmaInstance.kill();
            setSigmaInstance(null);
        }

        const graph = new Graph();
        const nodeSet = new Set(); // Store allowed nodes

        // Step 1️⃣: Add First 100 Nodes
        data.slice(0, 1000).forEach((row) => {
            const nodeId = row[0].toString();
            nodeSet.add(nodeId);

            graph.addNode(nodeId, {
                label: `Node ${nodeId}`,
                size: 5,
                color: "#007bff",
                x: Math.random() * 1000,
                y: Math.random() * 1000,
            });
        });

        // Step 2️⃣: Add Only Valid Edges (Both Nodes Must Be in the First 100)
        data.slice(0, 1000).forEach((row) => {
            const nodeId = row[0].toString();
            row.slice(1).forEach((neighbor) => {
                const neighborId = neighbor.toString();
                if (nodeSet.has(neighborId) && !graph.hasEdge(nodeId, neighborId)) {
                    graph.addEdge(nodeId, neighborId, { size: 1, color: "#aaa" });
                }
            });
        });

        // Step 3️⃣: Use WebGL-Optimized Layout
        const layout = new FA2LayoutSupervisor(graph, {
            settings: { barnesHutOptimize: true },
        });
        layout.start();

        // Step 4️⃣: Render Graph with Sigma.js
        const newSigmaInstance = new Sigma(graph, containerRef.current);
        setSigmaInstance(newSigmaInstance);

        return () => {
            layout.kill();
            newSigmaInstance.kill();
        };

    }, []);

    return <div ref={containerRef} className="w-full h-[80vh] bg-slate-100" />;
}

export default function GraphRenderer() {
    const [data, setData] = useState<number[][] | null>(null);

    useEffect(() => {
        fetchAndParseCSV().then((result) => {
            if (result) setData(result);
        });
    }, []);

    return (
        <div className="container mx-auto p-4">
            <div className="text-2xl font-bold mb-4">Graph Renderer</div>
            {data && <RenderGraph data={data} />}
        </div>
    );
}