import * as React from "react";

/**
 * The single text input pattern in the product — 12px padding, 8px radius, card fill,
 * 2px blue focus ring. Used for the child's name and the Wi-Fi password (with an eye toggle).
 */
export interface TextFieldProps {
  value: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  type?: "text" | "password";
  /** lucide node at 16×16, inset 12px from the left. */
  leadingIcon?: React.ReactNode;
  /** lucide node at 16×16 rendered as a button (Eye / EyeOff). */
  trailingIcon?: React.ReactNode;
  onTrailingClick?: () => void;
  /** Red border + caption when set. */
  error?: string | null;
  disabled?: boolean;
}

export declare function TextField(props: TextFieldProps): JSX.Element;
