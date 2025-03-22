import ResultDisplay from "./resultDisplay"

export default async function Page({
    params,
  }: {
    params: Promise<{ slug: string }>
  }) {
 
 
    const { slug } = await params
    return <ResultDisplay id={slug}/>
  }