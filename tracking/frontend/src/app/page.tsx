'use client'
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import { useState } from "react";
import Link from "next/link";

export default function Home() {
  return (
    <div>
      <div className="text-3xl m-2 my-4">Construction</div>
      <div className="space-y-4">
      <ConstructForm/>
      <AvailableIndexes/>
      </div> 
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

export interface Index {
  index_name: string;
  base_file: string;
  r: number;
  l_build: number;
  alpha: number;
  saturate_graph: boolean;
  id: string;
}

function AvailableIndexes(){
  const { data, loading, error } = useFetch<{indexes: Index[]}>("/list_indexes", "GET", undefined, {
    pollIntervalMs: 5000,
  });
  console.log(data)

  return <div>
    <div className="text-2xl">
      Available Indexes
    </div>
    {loading && <div>Loading...</div>}
    {error && <div className="text-red-500 mt-2">{error}</div>}
    {
      data && data.indexes.map((index, i) => (
        <div key={i} className="border-2 border-gray-200 p-3 py-5 rounded-md my-2">
          <div className="flex justify-between">
          <div className="text-xl font-bold mb-2 mx-1">{index.index_name}</div>
          <Button variant={"outline"} size={"lg"} asChild>
            <Link href={`/index/${index.index_name}`}>
              View
            </Link>
          </Button>
          </div>
          <div className="grid grid-cols-2 gap-4">
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Base File</div>
                  <div className="text-lg mx-1">{index.base_file}</div>
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Index Range (#Edges/Node)</div>
                  <div className="text-lg mx-1">{index.r}</div>
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">L Build (Search Depth during build)</div>
                  <div className="text-lg mx-1">{index.l_build}</div>
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Alpha α (Exponential Factor)</div>
                  <div className="text-lg mx-1">{index.alpha}</div>
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Saturate Edge Budget?</div>
                  <div className="text-lg mx-1">{index.saturate_graph ? "Yes" : "No"}</div>
              </div>
          </div>
        </div>
      ))
    }
  </div>
}