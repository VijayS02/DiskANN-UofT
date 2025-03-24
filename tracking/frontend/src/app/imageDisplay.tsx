import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
  } from "@/components/ui/card"
import {
    Carousel,
    CarouselContent,
    CarouselItem,
    CarouselNext,
    CarouselPrevious,
  } from "@/components/ui/carousel"
import Image from "next/image"

export default function ImageDisplay({url_base, image_metrics, full_col} : {url_base: string, image_metrics: string[], full_col?: boolean}) {
    console.log(`${url_base}/${image_metrics[0]}`)
    return <Card className={full_col ? "col-span-full" : ""}>
    <CardHeader>
        <CardTitle>Graphs</CardTitle>
        <CardDescription>Graphs extracted from tracing</CardDescription>
      </CardHeader>
      <CardContent className="relative">
        <Carousel className="w-full">
            <CarouselContent>
            {image_metrics.map((metric_id) => (
                <CarouselItem className={full_col ? "basis-1/3" : "w-full"} key={metric_id}>
                <div className="p-1">
                    <Image src={`${url_base}/${metric_id}`} className="w-full" width={500} height={500} alt="Image" />
                </div>
                </CarouselItem>
            ))}
            </CarouselContent>
            <CarouselPrevious  className="-left-4 disabled:opacity-25 bg-black text-white opacity-50 hover:bg-black hover:text-white hover:opacity-100"/>
            <CarouselNext  className="-right-4 disabled:opacity-25 bg-black text-white opacity-50 hover:bg-black hover:text-white hover:opacity-100"/>
        </Carousel>
    </CardContent>
  </Card>
}

// export default function ImageDisplay({url_base, image_metrics} : {url_base: string, image_metrics: string[]}) {
//     console.log(`${url_base}/${image_metrics[0]}`)
//     return image_metrics.map((metric_id) => (<Card key={metric_id}>
//       <CardContent className="relative">
//         <Carousel className="w-full">
//                 <div className="p-1">
//                     <Image src={`${url_base}/${metric_id}`} className="w-full" width={500} height={500} alt="Image" />
//                 </div>

//         </Carousel>
//     </CardContent>
//   </Card>))
// }