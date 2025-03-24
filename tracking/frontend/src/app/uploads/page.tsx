'use client'

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import useFetch from "@/util";

export default function Page(){

    return <div className="space-y-5">
        <div className="text-3xl m-2 my-4">
            Manage Uploads
        </div>
        <UploadForm/>
        <ListUploads/>
    </div>
}

function UploadForm(){
    const {data, loading, error, fetchData} = useFetch<any>("/upload", "POST");

    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
        if (loading) return;
        e.preventDefault();
        const formData = new FormData(e.currentTarget);
        fetchData(formData);
    }

    return <Card>
        <CardHeader>
            <div className="text-xl">
                Upload File
            </div>
        </CardHeader>
    <CardContent>
    <form onSubmit={handleSubmit} encType="multipart/form-data" className="grid grid-cols-2 gap-4">
        <Input type="file" name="file"/>
        <div>
        <Button type="submit" disabled={loading} >Upload</Button>
        </div>
    </form>
    </CardContent>
    <CardFooter>
        {loading && <div>Uploading...</div>}
        {error && <div>Error: {error}</div>}
        {data && <div className="text-green-700">File uploaded successfully</div>}
    </CardFooter>
    </Card>
}

// {
//     "files": [
//         "json.hpp",
//         "sift_learn.fbin",
//         "Figure_1.png"
//     ]
// }

function ListUploads(){
    const {data, loading, error} = useFetch<any>("/uploads", "GET");
    console.log(data)
    return <Card>
        <CardHeader>
            <div className="text-xl">
                Uploads
            </div>
        </CardHeader>
        <CardContent>
            <div className="space-y-3">
            {
                data && data?.files?.map((file: string) => <div key={file}>{file}</div>)
            }
            </div>
        </CardContent>
    </Card>
}

interface FileChooserProps {
    selectedFile: string;
    setSelectedFile: (index: string) => void;
    placeholder: string;
    label: string;
}

// interface fileData { 
//     files: string[]
// }


function FileChooser({ selectedFile, setSelectedFile, placeholder, label }: FileChooserProps) {
    const { data, loading, error } = useFetch<{files: string[]}>("/uploads", "GET", undefined, {
        pollIntervalMs: 5000,
      });

    return <div>
    <div className="text-muted-foreground mb-1 mx-1">{label}</div>
    <Select disabled={loading || data?.files.length == 0} value={selectedFile} onValueChange={setSelectedFile}>
      <SelectTrigger className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
          {data?.files.map((file) => (
            <SelectItem key={file} value={file}>
              {file}
            </SelectItem>
          ))}
      </SelectContent>
    </Select>
</div>
    
}

export {FileChooser};
