'use client'
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { useEffect, useRef } from "react";
import Sigma from "sigma";


export default function RenderGraph(){
    const containerRef = useRef<HTMLDivElement | null>(null);

    useEffect(() => {
      if (typeof window === "undefined") return;
      if (!containerRef.current) return;
  
      // Create the graph
      const graph = new Graph();
  
      // Add nodes (no x, y set yet)
      graph.addNode("A", { label: "Node A", size: 10, color: "blue" });
      graph.addNode("B", { label: "Node B", size: 20, color: "red" });
      graph.addNode("C", { label: "Node C", size: 15, color: "green" });
  
      // Add edges
      graph.addEdge("A", "B", { size: 5, color: "purple" });
      graph.addEdge("B", "C", { size: 5, color: "orange" });
      graph.addEdge("C", "A", { size: 5, color: "cyan" });
  
      // Initialize node positions with random values (to prevent NaN errors)
      graph.forEachNode((node) => {
        graph.mergeNodeAttributes(node, {
          x: Math.random() * 100,
          y: Math.random() * 100,
        });
      });
  
      // Run forceAtlas2 layout and update node positions
      forceAtlas2.assign(graph, {
        iterations: 100,
        settings: { gravity: 1, scalingRatio: 2 },
      });
  
      // Instantiate Sigma.js
      const sigmaInstance = new Sigma(graph, containerRef.current);
  
      return () => {
        sigmaInstance.kill(); // Cleanup
      };
    }, []);
  
    return <div ref={containerRef} className="w-full h-[80vh] bg-slate-100" />;
}