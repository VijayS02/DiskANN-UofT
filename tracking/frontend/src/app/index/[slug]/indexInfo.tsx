'use client'
import { Index } from "@/app/page";
import useFetch, { toSuperscript } from "@/util";

import {
    Table,
    TableBody,
    TableCaption,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
  } from "@/components/ui/table"
import Image from "next/image";
import ImageDisplay from "@/app/imageDisplay";


export default function IndexInfo({index_name} : {index_name: string}) {
    const { data, loading, error } = useFetch< Index>(`/index_json/${index_name}`);
    console.log(data)
    return (
    <div>
        <div className="text-2xl mb-3">Construction Details for <span className="font-bold">{index_name}</span></div>
        {loading && <div>Loading...</div>}
        {error && <div className="text-red-500 mt-2">{error}</div>}
        {data && <div>
            <div className="grid grid-cols-2 gap-4">
                <div className="col-span-full">
                    <IndexStatDisplay res={data} showMetrics/>
                </div>
                <ImageDisplay full_col url_base={`/api/index_image/${index_name}`} image_metrics={data.output_types['graph']}/>
            </div>
            
        </div>}
    </div>
)
}

function IndexStatDisplay({res, showMetrics} : {res: Index, showMetrics?: boolean}) {
  const { data, loading, error } = useFetch<Record<string, { label: string }>>("/construction_metrics");

  const selectedMetrics = data ? res.metrics.map((key) => {
    return data[key]?.label;
  }) : res.metrics;

    return <div className="border border-gray-200 rounded"> <Table className="px-3">
    <TableHeader>
      <TableRow>
        <TableHead className="w-[100px] text-sm text-muted-foreground">Parameter</TableHead>
        <TableHead className="text-right"></TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell className="font-medium">Base File Path</TableCell>
        <TableCell className="text-right">{res.base_file}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">Range</TableCell>
        <TableCell className="text-right">{res.r}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">L Build</TableCell>
        <TableCell className="text-right">{res.l_build}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">Alpha</TableCell>
        <TableCell className="text-right">{res.alpha}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">Number of Vectors</TableCell>
        <TableCell className="text-right">{`${res.n.toLocaleString()}  ∈  ℝ${toSuperscript(res.dimensions)}`}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell className="font-medium">Saturated Graph?</TableCell>
        <TableCell className="text-right">{res.saturate_graph ? "True" : "False"}</TableCell>
      </TableRow>
      {showMetrics && <TableRow>
        <TableCell className="font-medium">Metrics Tracked</TableCell>
        <TableCell className="text-right">
          <div className="justify-end flex divide-x-1">
            {selectedMetrics.map((metric, i) => (
              <div key={i} className={i !== selectedMetrics.length -1 ? "px-3" : "pl-3"}>{metric}</div>
            ))}
          </div>
        </TableCell>
      </TableRow>}
    </TableBody>
  </Table>
  </div>
 
}

export {IndexStatDisplay}