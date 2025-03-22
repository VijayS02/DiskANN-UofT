'use client'
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import { useState } from "react";

export default function Queries() {
  return (
    <div>
      <div className="text-3xl m-2 my-4">Queries</div>
      <div className="space-y-4">
      <QueryForm/>
      </div> 
    </div>
  );
}

const QueryForm: React.FC = () => {
  const [indexName, setIndexName] = useState("");
  const [queryFile, setQueryFile] = useState("");
  const [lQuery, setLquery] = useState<number | "">("");
  const [k, setK] = useState<number | "">("");

  const { data, loading, error, fetchData } = useFetch<any>("/query_index", "POST");

  const handleSubmit = () => {
      if (!indexName || !queryFile) {
          alert("Index Name and Query File are required!");
          return;
      }

      fetchData({
          index_name: indexName,
          query_file: queryFile,
          l: lQuery || 50,
          k: k || 10,
      });
  };

  return (
      <div className="w-full border-2 border-gray-200 p-3 py-5 rounded-md">
          <div className="text-xl mb-2 mx-1">Create Query</div>
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
                  <div className="text-muted-foreground mb-1 mx-1">Query File</div>
                  <Input 
                      placeholder="Enter base file path"
                      value={queryFile}
                      onChange={(e) => setQueryFile(e.target.value)}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">L (Search Depth)</div>
                  <Input 
                      placeholder="Enter L Query"
                      step="1"
                      type="number"
                      value={lQuery}
                      onChange={(e) => setLquery(e.target.value ? parseInt(e.target.value) : "")}
                  />
              </div>
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">K - How many neighbors</div>
                  <Input 
                      placeholder="Enter k"
                      type="number"
                      step="1"
                      value={k}
                      onChange={(e) => setK(e.target.value ? parseFloat(e.target.value) : "")}
                  />
              </div>
              <div className="flex p-2 space-between flex-col gap-2 max-w-1/2">
                  <Button size="sm" onClick={handleSubmit} disabled={loading}>
                      {loading ? "Submitting..." : "Query!"}
                  </Button>
              </div>
          </div>
          {error && <div className="text-red-500 mt-2">{error}</div>}
          {data && <div className="text-green-700 mt-2">Graph Creation initiated!</div>}
      </div>
  );
};