'use client'
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import Link from "next/link";


interface Status {
    buildDir: string;
}

function Navbar() {
    const { data, loading, error } = useFetch<Status>("/status", "GET", undefined, {
      pollIntervalMs: 5000,
    });
    
    return (
      <div className="w-full flex justify-center sticky top-0 h-16 shadow p-2">
        <div className="container flex justify-between">
          <div className="flex space-x-4">
            <div className="text-2xl my-auto">
              DiskANN Tracker
            </div>
            <div className="my-auto">
                <Pinger status={loading ? "loading" : error ? "error" : data?.buildDir ? "success" : "no_build"} />
            </div>
          </div>
          <div className="flex space-x-4 my-auto">
            <Button variant={'ghost'} size={'lg'} asChild><Link href="/">Construct</Link></Button>
            <Button variant={'ghost'} size={'lg'} asChild><Link href="/query">Query</Link></Button>
            <CreateBuild/>
          </div>
        </div>
      </div>
    );
  }
  

interface BuildResponse {
    buildDir: string;
}

function CreateBuild(){

    const { data, loading, error, fetchData } = useFetch<BuildResponse>(
        "/create_build"
    );

    console.log(loading);


    return <Button disabled={loading} onClick={(e) => {
        fetchData()
    }} size={'lg'}>Build</Button>
}

function Pinger({status}: { status: "loading" | "error" | "success" | "no_build"}){
    // Instead of string interpolation, use conditional classes
    const bgPingClass = status === "loading" 
      ? "bg-yellow-500 animate-ping" 
      : status === "error" 
        ? "bg-gray-500/20" 
        : status === 'no_build' ? 'bg-orange-500' : "bg-green-500 animate-ping";
        
    const bgDotClass = status === "loading"  
      ? "bg-yellow-500" 
      : status === "error"  
        ? "bg-gray-500/20" 
        : status === 'no_build' ? 'bg-orange-500' : "bg-green-500";

    return <span className="relative flex size-3">
    <span className={`absolute inline-flex h-full w-full duration-500 rounded-full opacity-75 ${bgPingClass}`}></span>
    <span className={`relative inline-flex size-3 rounded-full ${bgDotClass}`}></span>
  </span>
}


export default Navbar;