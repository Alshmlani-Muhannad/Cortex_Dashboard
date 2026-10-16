import { Fragment, PropsWithChildren } from "react";

export const Card = ({ children, className }: PropsWithChildren & { className?: string }) => (
  <section className={`soc-card ${className || ""}`}>{children}</section>
);
export const CardBody = ({ children, className }: PropsWithChildren & { className?: string }) => (
  <div className={`${className || ""}`}>{children}</div>
);
export const CardHeader = ({ children, className }: PropsWithChildren & { className?: string }) => (
  <div className={`mb-4 ${className || ""}`}>{children}</div>
);
export const CardFooter = ({ children, className }: PropsWithChildren & { className?: string }) => (
  <div className={`mt-4 pt-4 border-t border-soc-border/50 ${className || ""}`}>{children}</div>
);