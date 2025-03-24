'use client'
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import Link from "next/link";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
  } from "@/components/ui/tooltip"


interface Status {
    build_dir: string;
}

function Navbar() {
    const { data, loading, error } = useFetch<Status>("/status", "GET", undefined, {
      pollIntervalMs: 5000,
    });
    
    return (
      <div className="w-full z-[9] bg-background/20 backdrop-blur flex justify-center sticky top-0 h-16 shadow p-2">
        <div className="container flex justify-between">
          <div className="flex space-x-4">
            <div className="text-2xl my-auto">
              DiskANN Tracker
            </div>
            <div className="my-auto">
                <Pinger status={loading ? "loading" : error ? error === "423" ? "locked" : "error" : data?.build_dir === "NONE" ? "no_build" : "success"} />
            </div>
          </div>
          <div className="flex space-x-4 my-auto">
          <Button variant={'ghost'} size={'lg'} asChild><Link href="/uploads">Uploads</Link></Button>
            <Button variant={'ghost'} size={'lg'} asChild><Link href="/">Construct</Link></Button>
            <Button variant={'ghost'} size={'lg'} asChild><Link href="/query">Query</Link></Button>
            <CreateBuild/>
          </div>
        </div>
      </div>
    );
  }
  

function CreateBuild(){

    const { data, loading, error, fetchData } = useFetch<any>(
        "/create_build",
        "POST"
    );


    return <Button disabled={loading} onClick={(e) => {
        fetchData()
    }} size={'lg'}>Build</Button>
}

function Pinger({status}: { status: "loading" | "locked" | "error" | "success" | "no_build"}){
    const statusMap = {
        "loading": "Loading...",
        "locked": "Mutex Locked",
        "error": "Error",
        "success": "Build Ready",
        "no_build": "No Build"
    }

    const pingColors = {
        "loading": "bg-yellow-500 animate-pulse",
        "locked": "bg-purple-500/50 animate-pulse",
        "error": "bg-gray-500",
        "success": "bg-green-500 animate-pulse",
        "no_build": "bg-orange-500"
    }

    const dotColors = {
        "loading": "bg-yellow-500",
        "locked": "bg-purple-500/50",
        "error": "bg-gray-500",
        "success": "bg-green-500",
        "no_build": "bg-orange-500"
    }


    // Instead of string interpolation, use conditional classes
    const bgPingClass = pingColors[status]
        
    const bgDotClass = dotColors[status]

    return <TooltipProvider>
            <Tooltip>
                <TooltipTrigger asChild>
                    <div>
                    <span className="relative flex size-3">
                        <span className={`absolute inline-flex h-full w-full duration-500 rounded-full opacity-75 ${bgPingClass}`}></span>
                        <span className={`relative inline-flex size-3 rounded-full ${bgDotClass}`}></span>
                    </span>
                    </div>
                </TooltipTrigger>
                <TooltipContent>{statusMap[status]}</TooltipContent>
            </Tooltip>
    </TooltipProvider>
}


export default Navbar;