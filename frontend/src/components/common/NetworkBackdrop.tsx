import type { ReactNode } from "react";

export function NetworkBackdrop({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`network-backdrop ${className}`}>{children}</div>;
}
