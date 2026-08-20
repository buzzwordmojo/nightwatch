/** Threshold slider used across settings (audio gain, alert sensitivity, radar range). */
export interface SliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange?: (value: number) => void;
  /** Muted caption on the left of the track. */
  label?: string;
  /** Mono-set readout on the right; defaults to the raw value. */
  valueLabel?: string;
  disabled?: boolean;
}

export declare function Slider(props: SliderProps): JSX.Element;
