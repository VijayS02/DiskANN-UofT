'use client'
import { Input } from "@/components/ui/input";
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectLabel,
    SelectTrigger,
    SelectValue,
  } from "@/components/ui/select"
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import { useEffect, useState } from "react";
import { Index } from "../page";
import Image from "next/image";
import Link from "next/link";
import MultiSelect from "@/components/ui/multiselect";

export default function Queries() {
  return (
    <div>
      <div className="text-3xl m-2 my-4">Queries</div>
      <div className="space-y-4">
      <QueryForm/>
      <Results/>
      </div> 
      
    </div>
  );
}

const QueryForm: React.FC = () => {
  const [indexName, setIndexName] = useState("");
  const [queryFile, setQueryFile] = useState("");
  const [lQuery, setLquery] = useState<number | "">(50);
  const [k, setK] = useState<number | "">(10);
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>([]);

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
          metrics: selectedMetrics,
      });
  };

  return (
      <div className="w-full border-2 border-gray-200 p-3 py-5 rounded-md">
          <div className="text-xl mb-2 mx-1">Create Query</div>
          <div className="grid grid-cols-2 gap-4">
              <IndexSelector selectedIndex={indexName} setSelectedIndex={setIndexName} />
              <div>
                  <div className="text-muted-foreground mb-1 mx-1">Query File</div>
                  <Input 
                      placeholder="Enter query file path"
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
              <SelectMetrics selectedMetrics={selectedMetrics} setSelectedMetrics={setSelectedMetrics}/>
              <div className="flex p-2 space-between flex-col gap-2 justify-end max-w-1/2">
                  <Button size="sm" onClick={handleSubmit} disabled={loading}>
                      {loading ? "Submitting..." : "Query!"}
                  </Button>
              </div>
          </div>
          {error && <div className="text-red-500 mt-2">{error}</div>}
          {data && <div className="text-green-700 mt-2">Query initiated!</div>}
      </div>
  );
};

interface IndexSelectorProps {
    selectedIndex: string;
    setSelectedIndex: (value: string) => void;
}

function IndexSelector({ selectedIndex, setSelectedIndex }: IndexSelectorProps) {
    const { data, loading, error } = useFetch<{indexes: Index[]}>("/list_indexes", "GET", undefined, {
        pollIntervalMs: 5000,
      });

    return <div>
    <div className="text-muted-foreground mb-1 mx-1">Index Name</div>
    <Select disabled={loading || data?.indexes.length == 0} value={selectedIndex} onValueChange={setSelectedIndex}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder="Select an index" />
      </SelectTrigger>
      <SelectContent>
          {data?.indexes.map((index) => (
            <SelectItem key={index.index_name} value={index.index_name}>
              {index.index_name}
            </SelectItem>
          ))}
      </SelectContent>
    </Select>
</div>
    
}

function SelectMetrics({selectedMetrics, setSelectedMetrics} : any) {
  const { data, loading, error } = useFetch<Record<string, { label: string }>>("/query_metrics");

  const options = data ? Object.keys(data).map((key) => ({
    label: data[key]?.label,
    value: key,
  })) : [];

  useEffect(() => {
    // If data is loaded set default to all metrics
    if (data) {
      setSelectedMetrics(Object.keys(data));
    }
  }, [data]);

  console.log(data);


  return <div>
            <div className="text-muted-foreground mb-1 mx-1">Selected Metrics</div>
            <MultiSelect options={options} 
              disabled={loading}
              placeholder="Select metrics to track..." 
              selectedValues={selectedMetrics}
              setSelectedValues={setSelectedMetrics}
            />
          </div>

}

export interface ResultInfo {
    index_name: string;
    query_file: string;
    l: number;
    k: number;
    directory: string;
    id: string;
    data: any;
    metrics: string[];
}

function Results(){
  const { data, loading, error } = useFetch<{results: ResultInfo[]}>("/results_list", "GET", undefined, {
    pollIntervalMs: 5000,
  });


  return <div>
    <div className="text-2xl">
      Query Results
    </div>
    {loading && <div>Loading...</div>}
    {error && <div className="text-red-500 mt-2">{error}</div>}
    {
      <div className="space-y-3 grid grid-cols-2 gap-2 my-2">
      {data && data.results.map((index, i) => (
        <ResultView key={i} result={index}/>
      ))}
      </div>
    }
  </div>
}

function ResultView({result}: {result: ResultInfo}){
  function Stat({name, value} : {name: string, value: string}) {
    return <div>
        <div className="text-muted-foreground">{name}</div>
        <div className="text-sm">{value}</div>
        </div>
    }

  return <div className="border-2 border-gray-200 p-3 py-5 rounded-md">
    <div className="flex">
    <div className="text-lg font-bold">{result.id}</div>
    <Button size="sm" className="ml-auto" asChild>
      <Link href={`/query/${result.id}`}>
        View 
      </Link>
    </Button>
    </div>
    <div className="grid-cols-2 grid gap-x-1 gap-y-3 mb-4">
      <Stat name="Index Name" value={result.index_name}/>
      <Stat name="Query File" value={result.query_file}/>
      <Stat name="L (Scratch size)" value={result.l.toString()}/>
      <Stat name="K (Number of neighbors)" value={result.k.toString()}/>
      {/* <Stat name="Directory" value={result.directory}/> */}
    </div>
    
    {/* <Image src={`/api/query_image/${result.id}`} alt="Query Result" className="w-full mx-auto" width={500} height={500}/> */}
  </div>
}