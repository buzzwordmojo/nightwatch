import * as React from "react";

/** Selectable Wi-Fi network row in the hotspot portal. Selection = blue border + 2px halo. */
export interface NetworkRowProps {
  ssid: string;
  /** 0–100. ≥70 Strong (green), ≥40 Good (amber), below Weak (grey). */
  signal?: number;
  secured?: boolean;
  selected?: boolean;
  onSelect?: () => void;
  /** lucide Wifi / WifiOff at 16×16. */
  icon?: React.ReactNode;
  /** lucide Lock at 12×12. */
  lockIcon?: React.ReactNode;
}

export declare function NetworkRow(props: NetworkRowProps): JSX.Element;
