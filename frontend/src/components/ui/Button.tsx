import { forwardRef, ButtonHTMLAttributes } from "react";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement>>(
  ({ className, variant = "primary", disabled, children, ...props }, ref) => {
    const base = "soc-btn rounded text-sm font-medium transition disabled:opacity-50 disabled:pointer-events-none";
    const variants: Record<string, string> = {
      primary: "bg-soc-accent text-soc-dark hover:bg-cyan-400",
      ghost: "bg-transparent text-gray-300 hover:bg-soc-border hover:text-white border border-transparent",
      outline: "border border-soc-border text-gray-300 hover:bg-white/5",
      danger: "bg-red-900/20 text-red-400 border border-red-900/30 hover:bg-red-900/40",
      success: "bg-green-900/20 text-green-400 border border-green-900/30 hover:bg-green-900/40",
    };
    return (
      <button ref={ref} className={`${base} ${variants[variant]} ${className || ""}`} disabled={disabled} {...props}>
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";