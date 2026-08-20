import * as React from "react";

/**
 * Surface container. Status variants tint the fill and animate — the app uses them
 * so a glance across the room reads the room's state.
 * @startingPoint section="Core" subtitle="Card surfaces and status variants" viewport="700x260"
 */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** `warning` pulses slowly (2s), `critical` pulses fast (0.75s) with a red shadow. */
  variant?: "default" | "success" | "warning" | "critical";
}

export declare function Card(props: CardProps): JSX.Element;
export declare function CardHeader(props: React.HTMLAttributes<HTMLDivElement>): JSX.Element;
export declare function CardTitle(props: React.HTMLAttributes<HTMLHeadingElement>): JSX.Element;
export declare function CardDescription(props: React.HTMLAttributes<HTMLParagraphElement>): JSX.Element;
export declare function CardContent(props: React.HTMLAttributes<HTMLDivElement>): JSX.Element;
export declare function CardFooter(props: React.HTMLAttributes<HTMLDivElement>): JSX.Element;
