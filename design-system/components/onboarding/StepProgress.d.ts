/** Setup-wizard progress bar with the "Step n of m" caption underneath. */
export interface StepProgressProps {
  /** 1-based index. */
  current: number;
  total: number;
}

export declare function StepProgress(props: StepProgressProps): JSX.Element;
