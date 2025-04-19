import React, { useState } from "react";
import Plot from "./Plot";
import {
  Card,
  CardAction,
  CardContent,
  CardHeader,
  CardTitle,
} from "./ui/card";

import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// ✅ Define props for different graph types
interface LinePlotProps {
  title: string;
  data: number[];
  xLabel: string;
  yLabel: string;
}

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

const LinePlot: React.FC<LinePlotProps> = ({ title, data, xLabel, yLabel }) => {
  return (
    <div>
      <div>{title}</div>
      <Plot
        data={[
          {
            y: data[1],
            x: data[0],
            type: "scatter",
            mode: "lines",
            line: { color: "red" },
          },
        ]}
        layout={{
          title: { text: title },
          xaxis: { title: { text: xLabel } },
          yaxis: { title: { text: yLabel } },
          hovermode: "closest",
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
};

interface HistogramProps {
  title: string;
  data: number[];
  xLabel: string;
  yLabel: string;
  yLog?: boolean;
}

const HistogramPlot: React.FC<HistogramProps> = ({
  title,
  data,
  xLabel,
  yLabel,
  yLog,
}) => {
  // Temporary states for inputs (values change as user types)
  const [tempXMin, setTempXMin] = useState<string>("0");
  const [tempXMax, setTempXMax] = useState<string>("");
  const [tempNumBins, setTempNumBins] = useState<number>(50);

  // States that actually control the plot (updated only when button is clicked)
  const [xMin, setXMin] = useState<number | undefined>(0);
  const [xMax, setXMax] = useState<number | undefined>(undefined);
  const [numBins, setNumBins] = useState<number>(50);

  // Apply changes when the button is clicked
  const handleApplySettings = () => {
    setXMin(tempXMin === "" ? undefined : Number(tempXMin));
    setXMax(tempXMax === "" ? undefined : Number(tempXMax));
    setNumBins(tempNumBins);
  };

  // **Filter data within the selected range**
  const filteredData = data.filter(
    (value) =>
      (xMin === undefined || value >= xMin) &&
      (xMax === undefined || value <= xMax)
  );

  return (
    <div className="w-full h-full">
      {/* Controls */}
      <div className="flex flex-wrap gap-4 mb-4">
        <Input
          type="number"
          placeholder="X Min"
          value={tempXMin}
          onChange={(e) => setTempXMin(e.target.value)}
          className="w-24"
        />
        <Input
          type="number"
          placeholder="X Max"
          value={tempXMax}
          onChange={(e) => setTempXMax(e.target.value)}
          className="w-24"
        />
        <Input
          type="number"
          placeholder="Bins"
          value={tempNumBins}
          onChange={(e) => setTempNumBins(Number(e.target.value))}
          className="w-24"
        />
        <Button onClick={handleApplySettings}>Apply</Button>
      </div>

      {/* Histogram */}
      <Plot
        data={[
          {
            x: filteredData, // Pass filtered data instead of the whole dataset
            type: "histogram",
            marker: { color: "blue" },
            nbinsx: numBins, // Now bins are calculated over the filtered range
          },
        ]}
        layout={{
          title: { text: title },
          xaxis: {
            title: { text: xLabel },
            range:
              xMin !== undefined && xMax !== undefined
                ? [xMin, xMax]
                : undefined,
          },
          yaxis: {
            title: { text: yLabel },
            type: yLog ? "log" : "linear",
          },
          bargap: 0.05,
          hovermode: "closest",
        }}
        useResizeHandler
        style={{ width: "100%", height: "100%" }}
      />
    </div>
  );
};

// ✅ Map correct graph types
export const GraphMap = {
  line: LinePlot,
  hist: HistogramPlot, // Fixed from "histogram" to "hist"
};

// ✅ MsgPackGraphRenderer component
function RenderGraph({
  graphId,
  data,
}: {
  graphId: string;
  data: Record<string, unknown>;
}) {
  const graphData = data[graphId] as Record<string, unknown>;
  const metadata = graphData["metadata"] as
    | { type: string; props: any }
    | undefined;

  if (!metadata) {
    console.warn(`No metadata found for graph ${graphId}`);
    return null;
  }

  // ✅ Use the first metadata object (fixing array issue)
  const graphType = metadata?.type as keyof typeof GraphMap;

  // ✅ Check if graph type exists in GraphMap
  const GraphComponent = GraphMap[graphType];
  if (!GraphComponent) {
    console.warn(`Unknown graph type: ${graphType} for graph ${graphId}`);
    return null;
  }

  // ✅ Ensure props are correctly mapped
  const props = {
    title: metadata.props.title,
    xLabel: metadata.props.x,
    yLabel: metadata.props.y,
    yLog: metadata.props.ylog ?? false, // Default to false if undefined
    data: graphData["data"]["query_run"] as number[],
  };

  return (
    <div key={graphId}>
      <GraphComponent key={graphId} {...props} />
    </div>
  );
}

export default function MsgPackGraphRenderer({
  graphIds,
  data,
}: {
  graphIds: string[];
  data: Record<string, unknown>;
}) {
  const [selectedGraph, setSelectedGraph] = React.useState<string>(graphIds[0]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Interactive Graphs</CardTitle>
        <CardAction>
          <Select value={selectedGraph} onValueChange={setSelectedGraph}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select a graph" />
            </SelectTrigger>
            <SelectContent>
              {graphIds.map((graphId) => (
                <SelectItem key={graphId} value={graphId}>
                  {graphId}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent>
        {selectedGraph && <RenderGraph graphId={selectedGraph} data={data} />}
      </CardContent>
    </Card>
  );
}
