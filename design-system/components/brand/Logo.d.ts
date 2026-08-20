/**
 * The KnightWatcher lockup: shield mark with a crescent moon, plus the two-tone
 * camel-case wordmark (Knight in foreground, Watcher in brand blue).
 * @startingPoint section="Brand" subtitle="Logo lockup, mark, and wordmark" viewport="700x150"
 */
export interface LogoProps {
  /** Cap height of the mark in px; the wordmark scales from it. Default 32. */
  size?: number;
  variant?: "lockup" | "mark" | "wordmark";
  /** Override the accent (shield outline + "Watcher"). Defaults to brand purple. */
  accent?: string;
  /** Override the crescent fill. Defaults to brand yellow. */
  moon?: string;
  style?: React.CSSProperties;
}

export declare function Logo(props: LogoProps): JSX.Element;
