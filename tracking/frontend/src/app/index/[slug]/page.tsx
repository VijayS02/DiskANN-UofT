import IndexInfo from "./indexInfo"

export default async function Page({
    params,
  }: {
    params: Promise<{ slug: string }>
  }) {
 
 
    const { slug } = await params
    return <>
    <IndexInfo index_name={slug}/>
    </>
  }