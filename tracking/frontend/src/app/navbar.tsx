"use client";
import { Button } from "@/components/ui/button";
import useFetch from "@/util";
import Link from "next/link";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Progress } from "@/components/ui/progress";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  YAxis,
  Tooltip as RechartsTooltip,
} from "recharts";
import { useEffect, useState } from "react";

interface Status {
  build_dir: string;
  device_stats: DeviceStatsProps;
}

function Navbar() {
  const { data, loading, error } = useFetch<Status>(
    "/status",
    "GET",
    undefined,
    {
      pollIntervalMs: 5000,
    }
  );

  return (
    <div className="w-full z-[9] bg-background/20 backdrop-blur flex justify-center sticky top-0 h-16 shadow p-2">
      <div className="container flex justify-between">
        <div className="flex space-x-4">
          <div className="text-2xl my-auto">DiskANN Tracker</div>
          <div className="my-auto">
            <Pinger
              status={
                loading
                  ? "loading"
                  : error
                  ? error === "423"
                    ? "locked"
                    : "error"
                  : data?.build_dir === "NONE"
                  ? "no_build"
                  : "success"
              }
            />
          </div>
          {data && <DeviceStats2 device_stats={data.device_stats} />}
        </div>
        <div className="flex space-x-4 my-auto">
          <Button variant={"ghost"} size={"lg"} asChild>
            <Link href="/uploads">Uploads</Link>
          </Button>
          <Button variant={"ghost"} size={"lg"} asChild>
            <Link href="/">Construct</Link>
          </Button>
          <Button variant={"ghost"} size={"lg"} asChild>
            <Link href="/query">Query</Link>
          </Button>
          <CreateBuild />
        </div>
      </div>
    </div>
  );
}

interface DeviceStatsProps {
  cpu_percent: number;
  memory: {
    percent: number;
    total: number;
    used: number;
    available: number;
  };
}

function DeviceStats({ device_stats }: { device_stats: DeviceStatsProps }) {
  const { cpu_percent, memory } = device_stats;

  const formatGB = (bytes: number) => (bytes / 1e9).toFixed(1) + " GB";

  return (
    <TooltipProvider>
      <div className="flex space-x-4 items-center">
        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <div className="text-xs mb-1 text-muted-foreground font-medium">
                CPU Usage
              </div>
              <Progress
                value={cpu_percent}
                className="h-2 rounded bg-slate-200 rounded-[3px] w-[100px]"
              />
            </div>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>{cpu_percent.toFixed(1)}% CPU used</p>
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <div>
              <div className="text-xs mb-1 text-muted-foreground font-medium">
                Memory Usage
              </div>
              <Progress
                value={memory.percent}
                className="h-2 rounded bg-slate-200 rounded-[3px] w-[100px]"
              />
            </div>
          </TooltipTrigger>
          <TooltipContent side="top">
            <p>
              {formatGB(memory.used)} / {formatGB(memory.total)} used
            </p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}

function DeviceStats2({ device_stats }: { device_stats: DeviceStatsProps }) {
  const [history, setHistory] = useState<
    { cpu: number; mem: number; timestamp: number }[]
  >([]);

  useEffect(() => {
    setHistory((prev) => {
      const next = [
        ...prev,
        {
          cpu: device_stats.cpu_percent,
          mem: device_stats.memory.percent,
          timestamp: Date.now(),
        },
      ];
      return next.length > 50 ? next.slice(-50) : next;
    });
  }, [device_stats]);

  return (
    <div className="flex space-x-3 items-center">
      <div className="flex flex-col text-xs text-muted-foreground space-y-1">
        <ResponsiveContainer
          width={100}
          height={40}
          className="bg-slate-200 rounded"
        >
          <LineChart data={history}>
            <YAxis domain={[0, 100]} hide />
            <RechartsTooltip
              formatter={(value: number) => [`${value.toFixed(1)}%`, "CPU"]}
              labelFormatter={() => ""}
              cursor={{ stroke: "#888", strokeDasharray: "3 3" }}
              wrapperStyle={{
                marginTop: "20px", // pushes it down
                transform: "translateY(20px)", // optional: fine-tuned downward shift
                fontSize: "0.75rem", // optional: make it smaller
              }}
            />

            <Line type="monotone" dataKey="cpu" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="flex flex-col text-xs text-muted-foreground space-y-1">
        <ResponsiveContainer
          width={100}
          height={40}
          className="bg-slate-200 rounded"
        >
          <LineChart data={history}>
            <YAxis domain={[0, 100]} hide />
            <RechartsTooltip
              formatter={(value: number) => [`${value.toFixed(1)}%`, "Memory"]}
              labelFormatter={() => ""}
              cursor={{ stroke: "#888", strokeDasharray: "3 3" }}
              wrapperStyle={{
                marginTop: "20px", // pushes it down
                transform: "translateY(20px)", // optional: fine-tuned downward shift
                fontSize: "0.75rem", // optional: make it smaller
              }}
            />
            <Line type="monotone" dataKey="mem" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function CreateBuild() {
  const { data, loading, error, fetchData } = useFetch<any>(
    "/create_build",
    "POST"
  );

  return (
    <Button
      disabled={loading}
      onClick={(e) => {
        fetchData();
      }}
      size={"lg"}
    >
      Build
    </Button>
  );
}

function Pinger({
  status,
}: {
  status: "loading" | "locked" | "error" | "success" | "no_build";
}) {
  const statusMap = {
    loading: "Loading...",
    locked: "Mutex Locked",
    error: "Error",
    success: "Build Ready",
    no_build: "No Build",
  };

  const pingColors = {
    loading: "bg-yellow-500 animate-pulse",
    locked: "bg-purple-500/50 animate-pulse",
    error: "bg-gray-500",
    success: "bg-green-500 animate-pulse",
    no_build: "bg-orange-500",
  };

  const dotColors = {
    loading: "bg-yellow-500",
    locked: "bg-purple-500/50",
    error: "bg-gray-500",
    success: "bg-green-500",
    no_build: "bg-orange-500",
  };

  // Instead of string interpolation, use conditional classes
  const bgPingClass = pingColors[status];

  const bgDotClass = dotColors[status];

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div>
            <span className="relative flex size-3">
              <span
                className={`absolute inline-flex h-full w-full duration-500 rounded-full opacity-75 ${bgPingClass}`}
              ></span>
              <span
                className={`relative inline-flex size-3 rounded-full ${bgDotClass}`}
              ></span>
            </span>
          </div>
        </TooltipTrigger>
        <TooltipContent>{statusMap[status]}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

export default Navbar;
