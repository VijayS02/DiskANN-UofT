"use client";
import { usePathname } from "next/navigation";

import { ReactNode } from "react";

export default function PageRenderer({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const noContainerRoutes = ["/code"];
  const shouldUseContainer = !noContainerRoutes.includes(pathname);

  return shouldUseContainer ? (
    <div className="flex justify-center py-3">
      <div className="container">{children}</div>
    </div>
  ) : (
    <div className="h-[calc(100vh-4rem)]">{children}</div>
  );
}
