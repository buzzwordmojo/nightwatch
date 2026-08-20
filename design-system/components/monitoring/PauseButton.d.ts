import * as React from "react";

/**
 * Pause monitoring for a fixed window (5/15/30/60 min) — the "we're changing the sheets"
 * control. While paused it flips to an amber Resume button showing the countdown.
 */
export interface PauseButtonProps {
  isPaused?: boolean;
  remainingMinutes?: number;
  onPause?: (minutes: number) => void;
  onResume?: () => void;
  /** lucide Pause / Play nodes at 16×16. */
  pauseIcon?: React.ReactNode;
  playIcon?: React.ReactNode;
}

export declare function PauseButton(props: PauseButtonProps): JSX.Element;
