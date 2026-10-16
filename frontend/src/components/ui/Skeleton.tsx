import { PropsWithChildren } from "react";

export const Skeleton = ({ className, children }: PropsWithChildren & { className?: string }) => (
  <div className={`animate-pulse rounded bg-soc-border/40 ${className || ""}`}>{children}</div>
);