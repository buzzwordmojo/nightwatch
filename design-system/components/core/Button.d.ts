import * as React from "react";

/**
 * Primary action control. Mirrors the nightwatch shadcn button: 40px default height,
 * 6px radius, 14px medium label, colour-only hover.
 * @startingPoint section="Core" subtitle="Button variants and sizes" viewport="700x160"
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual treatment. `default` is the blue primary. */
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link" | "success" | "warning" | "danger";
  /** `icon` renders a 40×40 square. */
  size?: "default" | "sm" | "lg" | "icon";
}

export declare function Button(props: ButtonProps): JSX.Element;
