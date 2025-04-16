import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import useFetch from "@/util";

const GenerateRandomVectorsForm: React.FC = () => {
  const [dataType, setDataType] = useState("float");
  const [outputFile, setOutputFile] = useState("");
  const [ndims, setNdims] = useState<number | "">(128);
  const [npts, setNpts] = useState<number | "">(10000);
  const [norm, setNorm] = useState<number | "">(-1);
  const [randScaling, setRandScaling] = useState<number | "">(1);

  const { data, loading, error, fetchData } = useFetch<any>(
    "/uploads/generate_random_vectors",
    "POST"
  );

  const handleSubmit = () => {
    if (!outputFile || !ndims || !npts) {
      alert(
        "Output File, Number of Dimensions, and Number of Points are required!"
      );
      return;
    }

    if (!outputFile.endsWith(".fbin")) {
      alert("Output file name must end with .fbin");
      return;
    }

    fetchData({
      data_type: dataType,
      output_file: outputFile,
      ndims: ndims,
      npts: npts,
      norm: norm === "" ? -1 : norm,
      rand_scaling: randScaling === "" ? 1 : randScaling,
    });
  };

  return (
    <div className="w-full border-2 border-gray-200 p-3 py-5 rounded-md">
      <div className="text-xl mb-2 mx-1">Generate Random Vectors</div>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-muted-foreground mb-1 mx-1">Data Type</div>
          <Select value={dataType} onValueChange={setDataType}>
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select a type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="float">float</SelectItem>
              <SelectItem value="int8">int8</SelectItem>
              <SelectItem value="uint8">uint8</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <div className="text-muted-foreground mb-1 mx-1">
            Output File Name
          </div>
          <Input
            placeholder="e.g. vectors.fbin"
            value={outputFile}
            onChange={(e) => setOutputFile(e.target.value)}
          />
        </div>

        <div>
          <div className="text-muted-foreground mb-1 mx-1"># of Dimensions</div>
          <Input
            placeholder="e.g. 128"
            type="number"
            step="1"
            value={ndims}
            onChange={(e) =>
              setNdims(e.target.value ? parseInt(e.target.value) : "")
            }
          />
        </div>

        <div>
          <div className="text-muted-foreground mb-1 mx-1"># of Vectors</div>
          <Input
            placeholder="e.g. 10000"
            type="number"
            step="1"
            value={npts}
            onChange={(e) =>
              setNpts(e.target.value ? parseInt(e.target.value) : "")
            }
          />
        </div>

        <div>
          <div className="text-muted-foreground mb-1 mx-1">
            Vector Norm (Optional)
          </div>
          <Input
            placeholder="e.g. 2 or -1"
            type="number"
            value={norm}
            onChange={(e) =>
              setNorm(e.target.value === "" ? "" : parseInt(e.target.value))
            }
          />
        </div>

        <div>
          <div className="text-muted-foreground mb-1 mx-1">
            Random Scaling (Optional)
          </div>
          <Input
            placeholder="e.g. 1"
            type="number"
            value={randScaling}
            onChange={(e) =>
              setRandScaling(
                e.target.value === "" ? "" : parseInt(e.target.value)
              )
            }
          />
        </div>

        <div className="flex p-2 flex-col gap-2 justify-end">
          <Button size="sm" onClick={handleSubmit} disabled={loading}>
            {loading ? "Generating..." : "Generate"}
          </Button>
        </div>
      </div>
      {error && <div className="text-red-500 mt-2">{error}</div>}
      {data && (
        <div className="text-green-700 mt-2">
          Random vectors successfully generated!
        </div>
      )}
    </div>
  );
};

export default GenerateRandomVectorsForm;
