import * as React from "react";

/** Icon-circle + title + one-line description; the welcome step and landing page both use it. */
export interface FeatureItemProps {
  /** lucide node at 20×20 inside a 40px purple-tinted circle. */
  icon?: React.ReactNode;
  title: string;
  description: string;
}

export declare function FeatureItem(props: FeatureItemProps): JSX.Element;
