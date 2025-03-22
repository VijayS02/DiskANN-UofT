'use client'
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import { useState } from "react";

export default function Home() {
  return (
    <div>
      <div className="text-3xl m-2 my-4">Construction</div>
      <ConstructForm/>
    </div>
  );
}

const ConstructForm: React.FC = () => {
  const [indexName, setIndexName] = useState("");
  const [baseFile, setBaseFile] = useState("");
  const [r, setR] = useState<number | "">("");
  const [lBuild, setLBuild] = useState<number | "">("");
  const [alpha, setAlpha] = useState<number | "">("");
  const [saturateGraph, setSaturateGraph] = useState(true);

  const { data, loading, error, fetchData } = useFetch<any>("/create_graph", "POST");

  const handleSubmit = () => {
      if (!indexName || !baseFile) {
          alert("Index Name and Base File are required!");
          return;
      }

      fetchData({
          index_name: indexName,
          base_file: baseFile,
          r: r || 32, // Default value if empty
          l_build: lBuild || 50,
          alpha: alpha || 1.2,
          saturate_graph: saturateGraph,
      });
  };

  return (
      <div className="w-full border-2 border-gray-200 p-3 py-5 rounded-md">
          <div className="text-xl mb-2 mx-1">New Index</div>
          <div className="grid grid-cols-2 gap-4">
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Index Name</div>
                  <Input 
                      placeholder="Enter index name"
                      value={indexName}
                      onChange={(e) => setIndexName(e.target.value)}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Base File</div>
                  <Input 
                      placeholder="Enter base file path"
                      value={baseFile}
                      onChange={(e) => setBaseFile(e.target.value)}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Index Range (#Edges/Node)</div>
                  <Input 
                      placeholder="Enter range"
                      type="number"
                      value={r}
                      onChange={(e) => setR(e.target.value ? parseInt(e.target.value) : "")}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">L Build (Search Depth during build)</div>
                  <Input 
                      placeholder="Enter l_build"
                      type="number"
                      value={lBuild}
                      onChange={(e) => setLBuild(e.target.value ? parseInt(e.target.value) : "")}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Alpha α (Exponential Factor)</div>
                  <Input 
                      placeholder="Enter α"
                      type="number"
                      step="0.1"
                      value={alpha}
                      onChange={(e) => setAlpha(e.target.value ? parseFloat(e.target.value) : "")}
                  />
              </div>
              <div className="flex p-2 space-between flex-col gap-2 max-w-1/2">
                  <div className="flex items-center space-x-2">
                      <Checkbox 
                          id="saturate"
                          checked={saturateGraph}
                          onCheckedChange={(checked) => setSaturateGraph(!!checked)}
                      />
                      <label
                          htmlFor="saturate"
                          className="font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                      >
                          Saturate edge budget?
                      </label>
                  </div>
                  <Button size="sm" onClick={handleSubmit} disabled={loading}>
                      {loading ? "Submitting..." : "Submit"}
                  </Button>
              </div>
          </div>
          {error && <div className="text-red-500 mt-2">{error}</div>}
          {data && <div className="text-green-700 mt-2">Graph Creation initiated!</div>}
      </div>
  );
};
