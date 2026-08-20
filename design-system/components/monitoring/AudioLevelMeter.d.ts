/** Live microphone level with quarter ticks, scale labels, and an optional peak marker. */
export interface AudioLevelMeterProps {
  /** 0–1. */
  level: number;
  /** 0–1 decayed peak; the white hairline only draws when it leads the bar. */
  peak?: number;
}

export declare function AudioLevelMeter(props: AudioLevelMeterProps): JSX.Element;
