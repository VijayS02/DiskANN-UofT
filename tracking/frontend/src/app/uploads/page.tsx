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
  TableCaption,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

export default function Page() {
  return (
    <div className="space-y-5">
      <div className="text-3xl m-2 my-4">Manage Uploads</div>
      <UploadForm />
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
  const { data, loading, error } = useFetch<any>("/uploads", "GET");
  console.log(data);
  return (
    <Card>
      <CardHeader>
        <div className="text-xl">Uploads</div>
      </CardHeader>
      <CardContent>
        {loading && <div>Loading files...</div>}
        {error && <div className="text-red-500">Error: {error}</div>}

        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[200px]">Filename</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Type</TableHead>
              <TableHead className="text-right">Last Modified</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data?.files?.map((file: FileData) => (
              <TableRow key={file.filename}>
                <TableCell className="font-medium">{file.filename}</TableCell>
                <TableCell>{formatSize(file.size_bytes)}</TableCell>
                <TableCell>{file.mime_type}</TableCell>
                <TableCell className="text-right">
                  {new Date(file.modified).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
          {data?.files?.length > 0 && (
            <TableFooter>
              <TableRow>
                <TableCell colSpan={3}>Total files</TableCell>
                <TableCell className="text-right">
                  {data.files.length}
                </TableCell>
              </TableRow>
            </TableFooter>
          )}
        </Table>
      </CardContent>
    </Card>
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
