'use client'
import { Index } from "@/app/page";
import useFetch from "@/util";

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


export default function IndexInfo({index_name} : {index_name: string}) {
    const { data, loading, error } = useFetch< Index>(`/index_json/${index_name}`);
    console.log(data)
    return (
    <div>
        <div className="text-2xl mb-3">Construction Details for <span className="font-bold">{index_name}</span></div>
        {loading && <div>Loading...</div>}
        {error && <div className="text-red-500 mt-2">{error}</div>}
        {data && <div>
            <div className="grid grid-cols-2 gap-2">
                <div className="col-span-full">
                    <StatDisplay res={data}/>
                </div>
                <Image src={`/api/index_image/${index_name}`} className="w-full" alt="Query Image" width={500} height={500} />
            </div>
            
        </div>}
    </div>
)
}

function StatDisplay({res} : {res: Index}) {
    return <div className="border border-gray-200 rounded"> <Table className="px-3">
    <TableHeader>
      <TableRow>
        <TableHead className="w-[100px] text-sm text-muted-foreground">Parameter</TableHead>
        <TableHead className="text-right"></TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      <TableRow>
        <TableCell className="font-medium">Index Name</TableCell>
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
        <TableCell className="font-medium">Saturated Graph?</TableCell>
        <TableCell className="text-right">{res.saturate_graph ? "True" : "False"}</TableCell>
      </TableRow>
    </TableBody>
  </Table>
  </div>
 
}
