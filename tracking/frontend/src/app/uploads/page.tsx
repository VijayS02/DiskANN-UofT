"use client";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from "@/components/ui/select";
import useFetch from "@/util";
import { useState } from "react";
import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogTrigger,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogCancel,
  AlertDialogAction,
} from "@/components/ui/alert-dialog";
import { ArrowLeftRight, Trash } from "lucide-react";
import { Tooltip, TooltipTrigger } from "@/components/ui/tooltip";
import { TooltipContent, TooltipProvider } from "@radix-ui/react-tooltip";
import GenerateRandomVectorsForm from "./generateDataForm";

export default function Page() {
  return (
    <div className="space-y-5">
      <div className="text-3xl m-2 my-4">Manage Uploads</div>
      <UploadForm />
      <GenerateRandomVectorsForm />
      <ListUploads />
    </div>
  );
}

function UploadForm() {
  const [progress, setProgress] = useState(0);

  const { data, loading, error, fetchData } = useFetch<any>(
    "/upload",
    "POST",
    undefined,
    {
      onProgress: (percent: number) => setProgress(percent),
    }
  );

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    if (loading) return;
    e.preventDefault();
    setProgress(0); // Reset progress on new upload
    const formData = new FormData(e.currentTarget);
    fetchData(formData);
  };

  return (
    <Card>
      <CardHeader>
        <div className="text-xl">Upload File</div>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={handleSubmit}
          encType="multipart/form-data"
          className="grid grid-cols-2 gap-4"
        >
          <Input type="file" name="file" />
          <div>
            <Button type="submit" disabled={loading}>
              Upload
            </Button>
          </div>
        </form>
        {/* <div>Loading: {loading ? "1" : 0}</div> */}
        {/* Progress bar */}
        <div className="flex mt-5 items-center space-x-3">
          <Progress
            className={`w-1/2 transition-opacity duration-300`}
            value={progress}
          />
          <div>{progress}%</div>
        </div>
      </CardContent>

      <CardFooter>
        {progress === 100 && loading && (
          <div className="text-sm text-gray-500">Processing on server...</div>
        )}
        {error && <div className="text-red-500">Error: {error}</div>}
        {data && (
          <div className="text-green-700">File uploaded successfully</div>
        )}
      </CardFooter>
    </Card>
  );
}

// {
//     "files": [
//         "json.hpp",
//         "sift_learn.fbin",
//         "Figure_1.png"
//     ]
// }
// {
//     "filename": filename,
//     "size_bytes": size,
//     "mime_type": mime_type or "application/octet-stream",
//     "modified": modified_time,
// }

interface FileData {
  filename: string;
  size_bytes: number;
  mime_type: string;
  modified: string;
}

function formatSize(bytes: number) {
  const sizes = ["B", "KB", "MB", "GB"];
  if (bytes === 0) return "0 B";
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
}

function ListUploads() {
  const { data, loading, error } = useFetch<any>("/uploads", "GET", undefined, {
    pollIntervalMs: 3000,
  });

  const { loading: isDeleting, fetchData: deleteFile } = useFetch<any>(
    "/uploads/delete",
    "POST"
  );

  const { loading: isConverting, fetchData: fvecsToFbin } = useFetch<any>(
    "/uploads/fvecs_to_fbin",
    "POST"
  );

  const handleDeleteFile = (filename: string) => {
    deleteFile({ filename });
  };

  console.log(data);
  return (
    <Card>
      <CardHeader>
        <div className="text-xl">Uploads</div>
      </CardHeader>
      <CardContent>
        {loading && <div>Loading files...</div>}
        {error && <div className="text-red-500">Error: {error}</div>}
        <TooltipProvider>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Filename</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Type</TableHead>
                <TableHead className="text-right">Last Modified</TableHead>
                <TableHead className="text-right"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.files
                ?.sort(
                  (a: FileData, b: FileData) =>
                    new Date(b.modified).getTime() -
                    new Date(a.modified).getTime()
                )
                .map((file: FileData) => (
                  <TableRow key={file.filename}>
                    <TableCell className="font-medium">
                      {file.filename}
                    </TableCell>
                    <TableCell>{formatSize(file.size_bytes)}</TableCell>
                    <TableCell>{file.mime_type}</TableCell>
                    <TableCell className="text-right">
                      {new Date(file.modified).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end space-x-2">
                        {file.filename.endsWith(".fbin") && (
                          <SplitFile filename={file.filename} />
                        )}
                        {file.filename.endsWith(".fvecs") && (
                          <Tooltip>
                            <TooltipTrigger asChild>
                              <Button
                                disabled={isConverting}
                                onClick={(e) => {
                                  fvecsToFbin({ filename: file.filename });
                                }}
                              >
                                <ArrowLeftRight />
                              </Button>
                            </TooltipTrigger>
                            <TooltipContent className="bg-white shadow rounded p-2">
                              Convert to .fbin
                            </TooltipContent>
                          </Tooltip>
                        )}
                        <Button
                          disabled={isDeleting}
                          onClick={(e) => {
                            handleDeleteFile(file.filename);
                          }}
                          variant={"destructive"}
                        >
                          <Trash />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
            {data?.files?.length > 0 && (
              <TableFooter>
                <TableRow>
                  <TableCell colSpan={4}>Total files</TableCell>
                  <TableCell className="text-right">
                    {data.files.length}
                  </TableCell>
                </TableRow>
              </TableFooter>
            )}
          </Table>
        </TooltipProvider>
      </CardContent>
    </Card>
  );
}

export function SplitFile({ filename }: { filename: string }) {
  const [output1, setOutput1] = useState("output1.fbin");
  const [output2, setOutput2] = useState("output2.fbin");
  const [percentage, setPercentage] = useState(50);

  const {
    data,
    error,
    loading,
    fetchData: splitFile,
  } = useFetch<any>("/uploads/split_file", "POST");

  const handleConfirm = () => {
    splitFile({
      base_file: filename.replace(/\.bin$|\.fbin$/g, ""),
      output1: output1.replace(/\.bin$|\.fbin$/g, ""),
      output2: output2.replace(/\.bin$|\.fbin$/g, ""),
      percentage: percentage,
    });
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline">Split File</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Split File</AlertDialogTitle>
          <AlertDialogDescription>
            This will split <strong>{filename}</strong> into two files with a{" "}
            {percentage}%/{100 - percentage}% split.
          </AlertDialogDescription>
        </AlertDialogHeader>

        <div className="space-y-2 py-2">
          <Input
            value={output1}
            onChange={(e) => setOutput1(e.target.value)}
            placeholder="Output File 1"
          />
          <Input
            value={output2}
            onChange={(e) => setOutput2(e.target.value)}
            placeholder="Output File 2"
          />
          <Input
            type="number"
            value={percentage}
            onChange={(e) => setPercentage(parseInt(e.target.value))}
            min={1}
            max={99}
            placeholder="Percentage for Output 1"
          />
        </div>

        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={handleConfirm} disabled={loading}>
            {loading ? "Splitting..." : "Confirm"}
          </AlertDialogAction>
        </AlertDialogFooter>

        {data && (
          <div className="text-green-600 text-sm pt-2">Split complete!</div>
        )}
        {error && (
          <div className="text-red-600 text-sm pt-2">Error: {error}</div>
        )}
      </AlertDialogContent>
    </AlertDialog>
  );
}

interface FileChooserProps {
  selectedFile: string;
  setSelectedFile: (index: string) => void;
  placeholder: string;
  label: string;
  filterExt: string | null;
}

// interface fileData {
//     files: string[]
// }

function FileChooser({
  selectedFile,
  setSelectedFile,
  placeholder,
  label,
  filterExt = ".fbin",
}: FileChooserProps) {
  const { data, loading, error } = useFetch<{ files: FileData[] }>(
    "/uploads",
    "GET",
    undefined,
    {
      pollIntervalMs: 5000,
    }
  );

  return (
    <div>
      <div className="text-muted-foreground mb-1 mx-1">{label}</div>
      <Select
        disabled={loading || data?.files.length == 0}
        value={selectedFile}
        onValueChange={setSelectedFile}
      >
        <SelectTrigger className="w-full">
          <SelectValue placeholder={placeholder} />
        </SelectTrigger>
        <SelectContent>
          {data?.files
            .filter(
              (file) => filterExt === null || file.filename.endsWith(filterExt)
            )
            .map((file) => (
              <SelectItem key={file.filename} value={file.filename}>
                {file.filename}
              </SelectItem>
            ))}
        </SelectContent>
      </Select>
    </div>
  );
}

export { FileChooser };
