/* @ds-bundle: {"format":4,"namespace":"KnightWatcherDesignSystem_3ee9cb","components":[{"name":"Logo","sourcePath":"components/brand/Logo.jsx"},{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"CardHeader","sourcePath":"components/core/Card.jsx"},{"name":"CardTitle","sourcePath":"components/core/Card.jsx"},{"name":"CardDescription","sourcePath":"components/core/Card.jsx"},{"name":"CardContent","sourcePath":"components/core/Card.jsx"},{"name":"CardFooter","sourcePath":"components/core/Card.jsx"},{"name":"Progress","sourcePath":"components/core/Progress.jsx"},{"name":"Slider","sourcePath":"components/core/Slider.jsx"},{"name":"StatusIndicator","sourcePath":"components/core/StatusIndicator.jsx"},{"name":"AlertBanner","sourcePath":"components/monitoring/AlertBanner.jsx"},{"name":"AudioLevelMeter","sourcePath":"components/monitoring/AudioLevelMeter.jsx"},{"name":"EventRow","sourcePath":"components/monitoring/EventRow.jsx"},{"name":"PauseButton","sourcePath":"components/monitoring/PauseButton.jsx"},{"name":"SensorStatusBar","sourcePath":"components/monitoring/SensorStatusBar.jsx"},{"name":"VitalCard","sourcePath":"components/monitoring/VitalCard.jsx"},{"name":"FeatureItem","sourcePath":"components/onboarding/FeatureItem.jsx"},{"name":"NetworkRow","sourcePath":"components/onboarding/NetworkRow.jsx"},{"name":"SensorItem","sourcePath":"components/onboarding/SensorItem.jsx"},{"name":"StepProgress","sourcePath":"components/onboarding/StepProgress.jsx"},{"name":"TextField","sourcePath":"components/onboarding/TextField.jsx"}],"sourceHashes":{"components/brand/Logo.jsx":"68193e165096","components/core/Badge.jsx":"657bcf424540","components/core/Button.jsx":"38586afbe600","components/core/Card.jsx":"7a55a87d33ac","components/core/Progress.jsx":"14279bfc4b83","components/core/Slider.jsx":"6796211f86ea","components/core/StatusIndicator.jsx":"d2f4583757eb","components/monitoring/AlertBanner.jsx":"092eac4556c7","components/monitoring/AudioLevelMeter.jsx":"60e0afa3b677","components/monitoring/EventRow.jsx":"1fec5c01daed","components/monitoring/PauseButton.jsx":"b495cb8d707c","components/monitoring/SensorStatusBar.jsx":"25f6a6a7742c","components/monitoring/VitalCard.jsx":"b593026b2e01","components/onboarding/FeatureItem.jsx":"cd2c94cd9818","components/onboarding/NetworkRow.jsx":"e0713dd893fb","components/onboarding/SensorItem.jsx":"39221d686bdc","components/onboarding/StepProgress.jsx":"6c3a9e990c8d","components/onboarding/TextField.jsx":"4da1ed00d6bc","ui_kits/dashboard/DashboardScreen.jsx":"2ae592a5f36f","ui_kits/dashboard/PortalScreen.jsx":"b317bff20340","ui_kits/dashboard/SettingsScreen.jsx":"acbf01fff7d1","ui_kits/dashboard/SetupScreen.jsx":"6cda867e674f","ui_kits/dashboard/icon.jsx":"67329fd856e1","ui_kits/marketing/LandingPage.jsx":"c1e22f91943f"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.KnightWatcherDesignSystem_3ee9cb = window.KnightWatcherDesignSystem_3ee9cb || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/brand/Logo.jsx
try { (() => {
function Logo({
  size = 32,
  variant = "lockup",
  accent = "var(--brand-purple)",
  moon = "var(--brand-yellow)",
  style
}) {
  const mark = /*#__PURE__*/React.createElement("svg", {
    viewBox: "0 0 48 56",
    width: size * 0.857,
    height: size,
    fill: "none",
    style: {
      flexShrink: 0
    },
    "aria-hidden": "true"
  }, /*#__PURE__*/React.createElement("path", {
    d: "M24 2.6 44.4 11.2v18.4c0 13.1-9 21.7-20.4 25.4C12.6 51.3 3.6 42.7 3.6 29.6V11.2z",
    stroke: accent,
    strokeWidth: "3.4",
    strokeLinejoin: "round"
  }), /*#__PURE__*/React.createElement("path", {
    d: "M27.6 17.6a10 10 0 1 0 0 20 12.6 12.6 0 0 1 0-20z",
    fill: moon
  }));
  const word = /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-display)",
      fontWeight: "var(--weight-bold)",
      fontSize: size * 0.72,
      letterSpacing: "var(--tracking-tight)",
      lineHeight: 1,
      whiteSpace: "nowrap"
    }
  }, "Knight", /*#__PURE__*/React.createElement("span", {
    style: {
      color: accent
    }
  }, "Watcher"));
  return /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: size * 0.35,
      color: "var(--text-primary)",
      ...style
    }
  }, variant !== "wordmark" && mark, variant !== "mark" && word);
}
Object.assign(__ds_scope, { Logo });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/brand/Logo.jsx", error: String((e && e.message) || e) }); }

// components/core/Badge.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const TONES = {
  neutral: {
    background: "var(--surface-muted)",
    color: "var(--text-muted)"
  },
  accent: {
    background: "var(--fill-accent)",
    color: "var(--accent-primary)"
  },
  normal: {
    background: "rgba(22,163,74,.20)",
    color: "var(--status-normal)"
  },
  warning: {
    background: "rgba(250,204,21,.20)",
    color: "var(--status-warning)"
  },
  critical: {
    background: "rgba(239,68,68,.20)",
    color: "var(--status-critical)"
  },
  simulated: {
    background: "var(--status-simulated)",
    color: "var(--text-inverse)"
  }
};
function Badge({
  tone = "neutral",
  uppercase = false,
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("span", _extends({}, rest, {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 4,
      padding: uppercase ? "2px 6px" : "4px 8px",
      borderRadius: "var(--radius-sm)",
      fontFamily: "var(--font-body)",
      fontSize: uppercase ? "var(--text-2xs)" : "var(--text-xs)",
      fontWeight: uppercase ? "var(--weight-bold)" : "var(--weight-medium)",
      textTransform: uppercase ? "uppercase" : "none",
      letterSpacing: uppercase ? "var(--tracking-wide)" : "var(--tracking-normal)",
      lineHeight: 1.4,
      ...(TONES[tone] || TONES.neutral),
      ...style
    }
  }), children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const SIZES = {
  default: {
    height: 40,
    padding: "0 16px"
  },
  sm: {
    height: 36,
    padding: "0 12px"
  },
  lg: {
    height: 44,
    padding: "0 32px"
  },
  icon: {
    height: 40,
    width: 40,
    padding: 0
  }
};
const VARIANTS = {
  default: {
    background: "var(--accent-primary)",
    color: "var(--text-on-accent)",
    border: "1px solid transparent"
  },
  destructive: {
    background: "var(--red-600)",
    color: "#fff",
    border: "1px solid transparent"
  },
  outline: {
    background: "transparent",
    color: "var(--text-primary)",
    border: "1px solid var(--border-default)"
  },
  secondary: {
    background: "var(--surface-muted)",
    color: "var(--text-primary)",
    border: "1px solid transparent"
  },
  ghost: {
    background: "transparent",
    color: "var(--text-primary)",
    border: "1px solid transparent"
  },
  link: {
    background: "transparent",
    color: "var(--accent-primary)",
    border: "1px solid transparent",
    textDecoration: "underline",
    textUnderlineOffset: 4
  },
  success: {
    background: "var(--status-normal)",
    color: "#fff",
    border: "1px solid transparent"
  },
  warning: {
    background: "var(--status-warning)",
    color: "#000",
    border: "1px solid transparent"
  },
  danger: {
    background: "var(--status-critical)",
    color: "#fff",
    border: "1px solid transparent"
  }
};
function Button({
  variant = "default",
  size = "default",
  disabled,
  style,
  children,
  ...rest
}) {
  const [hover, setHover] = React.useState(false);
  const v = VARIANTS[variant] || VARIANTS.default;
  return /*#__PURE__*/React.createElement("button", _extends({}, rest, {
    disabled: disabled,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false),
    style: {
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      gap: 8,
      whiteSpace: "nowrap",
      borderRadius: "var(--radius-md)",
      fontFamily: "var(--font-body)",
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)",
      transition: "background var(--dur-fast) var(--ease-standard), color var(--dur-fast) var(--ease-standard), border-color var(--dur-fast) var(--ease-standard)",
      cursor: disabled ? "not-allowed" : "pointer",
      opacity: disabled ? 0.5 : 1,
      filter: hover && !disabled && variant !== "outline" && variant !== "ghost" && variant !== "link" ? "brightness(0.9)" : "none",
      ...(hover && !disabled && (variant === "outline" || variant === "ghost") ? {
        background: "var(--surface-muted)"
      } : null),
      ...SIZES[size],
      ...v,
      ...style
    }
  }), children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const VARIANTS = {
  default: {
    borderColor: "var(--border-default)",
    background: "var(--surface-card)"
  },
  success: {
    borderColor: "var(--border-normal)",
    background: "var(--fill-normal)"
  },
  warning: {
    borderColor: "var(--border-warning)",
    background: "var(--fill-warning)",
    animation: "kw-pulse-slow var(--dur-pulse-slow) var(--ease-standard) infinite"
  },
  critical: {
    borderColor: "var(--border-critical)",
    background: "var(--fill-critical)",
    animation: "kw-pulse-fast var(--dur-pulse-fast) var(--ease-standard) infinite",
    boxShadow: "var(--shadow-critical)"
  }
};
function Card({
  variant = "default",
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      borderRadius: "var(--radius-lg)",
      border: "1px solid",
      color: "var(--text-primary)",
      boxShadow: "var(--shadow-sm)",
      transition: "all var(--dur-slow) var(--ease-standard)",
      ...(VARIANTS[variant] || VARIANTS.default),
      ...style
    }
  }), children);
}
function CardHeader({
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 6,
      padding: 24,
      ...style
    }
  }), children);
}
function CardTitle({
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("h3", _extends({}, rest, {
    style: {
      margin: 0,
      fontFamily: "var(--font-display)",
      fontSize: "var(--text-2xl)",
      fontWeight: "var(--weight-semibold)",
      lineHeight: "var(--leading-none)",
      letterSpacing: "var(--tracking-tight)",
      ...style
    }
  }), children);
}
function CardDescription({
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("p", _extends({}, rest, {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      ...style
    }
  }), children);
}
function CardContent({
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      padding: "0 24px 24px",
      ...style
    }
  }), children);
}
function CardFooter({
  style,
  children,
  ...rest
}) {
  return /*#__PURE__*/React.createElement("div", _extends({}, rest, {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "0 24px 24px",
      ...style
    }
  }), children);
}
Object.assign(__ds_scope, { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/Progress.jsx
try { (() => {
function Progress({
  value = 0,
  tone = "accent",
  height = 8,
  style
}) {
  const pct = Math.min(100, Math.max(0, value));
  const fill = {
    accent: "var(--accent-primary)",
    normal: "var(--status-normal)",
    warning: "var(--status-warning)",
    critical: "var(--status-critical)"
  }[tone] || "var(--accent-primary)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height,
      width: "100%",
      overflow: "hidden",
      borderRadius: "var(--radius-full)",
      background: "var(--surface-muted)",
      ...style
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      width: pct + "%",
      background: fill,
      borderRadius: "var(--radius-full)",
      transition: "width var(--dur-base) var(--ease-standard)"
    }
  }));
}
Object.assign(__ds_scope, { Progress });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Progress.jsx", error: String((e && e.message) || e) }); }

// components/core/Slider.jsx
try { (() => {
function Slider({
  value = 50,
  min = 0,
  max = 100,
  step = 1,
  onChange,
  label,
  valueLabel,
  disabled
}) {
  const pct = (value - min) / (max - min) * 100;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      width: "100%",
      opacity: disabled ? 0.5 : 1
    }
  }, (label || valueLabel) && /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      marginBottom: 8,
      fontSize: "var(--text-sm)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--text-muted)"
    }
  }, label), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)",
      color: "var(--text-primary)"
    }
  }, valueLabel ?? value)), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height: 20,
      display: "flex",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: "auto 0",
      height: 6,
      borderRadius: "var(--radius-full)",
      background: "var(--surface-muted)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      left: 0,
      width: pct + "%",
      height: 6,
      borderRadius: "var(--radius-full)",
      background: "var(--accent-primary)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      left: `calc(${pct}% - 8px)`,
      width: 16,
      height: 16,
      borderRadius: "var(--radius-full)",
      background: "var(--text-primary)",
      border: "2px solid var(--accent-primary)",
      boxShadow: "var(--shadow-sm)"
    }
  }), /*#__PURE__*/React.createElement("input", {
    type: "range",
    value: value,
    min: min,
    max: max,
    step: step,
    disabled: disabled,
    onChange: e => onChange && onChange(Number(e.target.value)),
    style: {
      position: "absolute",
      inset: 0,
      width: "100%",
      opacity: 0,
      cursor: disabled ? "not-allowed" : "pointer",
      margin: 0
    }
  })));
}
Object.assign(__ds_scope, { Slider });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Slider.jsx", error: String((e && e.message) || e) }); }

// components/core/StatusIndicator.jsx
try { (() => {
const COLORS = {
  online: "var(--status-normal)",
  normal: "var(--status-normal)",
  warning: "var(--status-warning)",
  degraded: "var(--status-warning)",
  stale: "var(--status-warning)",
  error: "var(--status-critical)",
  alert: "var(--status-critical)",
  critical: "var(--status-critical)",
  offline: "var(--status-critical)"
};
const SIZES = {
  sm: 8,
  md: 12,
  lg: 16
};
function StatusIndicator({
  status = "offline",
  label,
  size = "md"
}) {
  const live = status === "normal" || status === "online";
  const d = SIZES[size] || SIZES.md;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: d,
      height: d,
      borderRadius: "var(--radius-full)",
      flexShrink: 0,
      background: COLORS[status] || "var(--status-offline)",
      animation: live ? "kw-pulse-ring var(--dur-pulse-slow) var(--ease-standard) infinite" : status === "stale" ? "kw-pulse-slow 2s var(--ease-standard) infinite" : "none"
    }
  }), label && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      textTransform: "capitalize"
    }
  }, label, ": ", status));
}
Object.assign(__ds_scope, { StatusIndicator });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/StatusIndicator.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/AlertBanner.jsx
try { (() => {
function AlertBanner({
  level = "warning",
  message,
  source,
  time,
  acknowledged,
  icon,
  onAcknowledge,
  onResolve
}) {
  const critical = level === "critical";
  const color = critical ? "var(--status-critical)" : "var(--status-warning)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 16,
      padding: 16,
      borderRadius: "var(--radius-lg)",
      border: "1px solid " + (critical ? "var(--border-critical)" : "var(--border-warning)"),
      background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)",
      animation: acknowledged ? "none" : "kw-pulse-slow 1s var(--ease-standard) infinite"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color,
      display: "inline-flex"
    }
  }, icon), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)",
      color
    }
  }, message), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, source, time ? " • " + time : "", acknowledged ? " • Acknowledged" : ""))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 8,
      flexShrink: 0
    }
  }, !acknowledged && /*#__PURE__*/React.createElement(__ds_scope.Button, {
    variant: "outline",
    size: "sm",
    onClick: onAcknowledge
  }, "Acknowledge"), /*#__PURE__*/React.createElement(__ds_scope.Button, {
    variant: critical ? "danger" : "warning",
    size: "sm",
    onClick: onResolve
  }, "Resolve")));
}
Object.assign(__ds_scope, { AlertBanner });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/AlertBanner.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/AudioLevelMeter.jsx
try { (() => {
function AudioLevelMeter({
  level = 0,
  peak
}) {
  const pct = Math.min(100, Math.max(0, level * 100));
  const peakPct = peak != null ? Math.min(100, Math.max(0, peak * 100)) : 0;
  const color = pct > 70 ? "var(--status-critical)" : pct > 40 ? "var(--status-warning)" : "var(--status-normal)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement("span", null, "Audio Level"), /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: "var(--font-mono)"
    }
  }, pct.toFixed(0), "%")), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative",
      height: 12,
      borderRadius: "var(--radius-full)",
      overflow: "hidden",
      background: "var(--surface-muted)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: 0,
      bottom: 0,
      left: 0,
      width: pct + "%",
      background: color,
      borderRadius: "var(--radius-full)",
      transition: "width 75ms linear"
    }
  }), peakPct > pct + 2 && /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      top: 0,
      bottom: 0,
      width: 2,
      left: peakPct + "%",
      background: "rgba(255,255,255,.7)"
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      inset: 0,
      display: "flex"
    }
  }, [0, 1, 2].map(i => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      flex: 1,
      borderRight: "1px solid rgba(2,8,23,.2)"
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "space-between",
      fontSize: "var(--text-2xs)",
      color: "rgba(148,163,184,.6)",
      padding: "0 2px"
    }
  }, ["0", "25", "50", "75", "100"].map(t => /*#__PURE__*/React.createElement("span", {
    key: t
  }, t))));
}
Object.assign(__ds_scope, { AudioLevelMeter });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/AudioLevelMeter.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/EventRow.jsx
try { (() => {
const SOURCE_LABELS = {
  radar: "Breathing",
  audio: "Audio",
  bcg: "Heart Rate",
  movement: "Movement"
};
function EventRow({
  source,
  level = "warning",
  message,
  startTime,
  endTime,
  duration,
  ongoing,
  count = 1,
  icon
}) {
  const critical = level === "critical" || level === "alert";
  const color = critical ? "var(--status-critical)" : "var(--status-warning)";
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: 12,
      padding: 12,
      borderRadius: "var(--radius-lg)",
      border: "1px solid " + (critical ? "rgba(239,68,68,.30)" : "rgba(250,204,21,.30)"),
      background: critical ? "var(--fill-critical)" : "var(--fill-warning)",
      animation: ongoing ? "kw-pulse-slow var(--dur-pulse-slow) var(--ease-standard) infinite" : "none"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      padding: 8,
      borderRadius: "var(--radius-full)",
      flexShrink: 0,
      background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)",
      color
    }
  }, icon), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--weight-medium)",
      color
    }
  }, SOURCE_LABELS[source] || source), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-xs)",
      textTransform: "uppercase",
      padding: "2px 8px",
      borderRadius: "var(--radius-full)",
      background: critical ? "rgba(239,68,68,.20)" : "rgba(250,204,21,.20)",
      color
    }
  }, level)), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      overflow: "hidden",
      textOverflow: "ellipsis",
      whiteSpace: "nowrap"
    }
  }, message), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      marginTop: 4,
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement("span", null, startTime), ongoing ? /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: "var(--weight-medium)",
      color
    }
  }, "ongoing") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("span", null, "-"), /*#__PURE__*/React.createElement("span", null, endTime), duration && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "rgba(248,250,252,.6)"
    }
  }, "(", duration, ")")), count > 1 && /*#__PURE__*/React.createElement("span", {
    style: {
      color: "rgba(248,250,252,.4)"
    }
  }, "\u2022 ", count, " events"))));
}
Object.assign(__ds_scope, { EventRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/EventRow.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/PauseButton.jsx
try { (() => {
const OPTIONS = [{
  minutes: 5,
  label: "Pause for 5 minutes"
}, {
  minutes: 15,
  label: "Pause for 15 minutes"
}, {
  minutes: 30,
  label: "Pause for 30 minutes"
}, {
  minutes: 60,
  label: "Pause for 1 hour"
}];
function PauseButton({
  isPaused,
  remainingMinutes,
  onPause,
  onResume,
  pauseIcon,
  playIcon
}) {
  const [open, setOpen] = React.useState(false);
  if (isPaused) {
    return /*#__PURE__*/React.createElement(__ds_scope.Button, {
      variant: "warning",
      size: "sm",
      onClick: onResume
    }, playIcon, "Resume (", remainingMinutes, "m)");
  }
  return /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, /*#__PURE__*/React.createElement(__ds_scope.Button, {
    variant: "outline",
    size: "sm",
    onClick: () => setOpen(!open)
  }, pauseIcon, "Pause"), open && /*#__PURE__*/React.createElement("div", {
    style: {
      position: "absolute",
      right: 0,
      top: "calc(100% + 4px)",
      zIndex: 20,
      minWidth: 190,
      padding: 4,
      borderRadius: "var(--radius-md)",
      border: "1px solid var(--border-default)",
      background: "var(--surface-card)",
      boxShadow: "var(--shadow-lg)"
    }
  }, OPTIONS.map(o => /*#__PURE__*/React.createElement("button", {
    key: o.minutes,
    onClick: () => {
      setOpen(false);
      onPause && onPause(o.minutes);
    },
    style: {
      display: "block",
      width: "100%",
      textAlign: "left",
      padding: "6px 8px",
      borderRadius: "var(--radius-sm)",
      border: "none",
      background: "transparent",
      color: "var(--text-primary)",
      fontFamily: "var(--font-body)",
      fontSize: "var(--text-sm)",
      cursor: "pointer"
    },
    onMouseEnter: e => e.currentTarget.style.background = "var(--surface-muted)",
    onMouseLeave: e => e.currentTarget.style.background = "transparent"
  }, o.label))));
}
Object.assign(__ds_scope, { PauseButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/PauseButton.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/SensorStatusBar.jsx
try { (() => {
function dotColor(sensor, mock) {
  if (mock) return "var(--status-simulated)";
  if (!sensor || !sensor.connected) return "rgba(148,163,184,.5)";
  if (["running", "online", "normal"].includes(sensor.status)) return "var(--status-normal)";
  if (["warning", "degraded", "uncertain"].includes(sensor.status)) return "var(--status-warning)";
  if (["error", "critical", "alert"].includes(sensor.status)) return "var(--status-critical)";
  return "rgba(148,163,184,.5)";
}
function SensorStatusBar({
  sensors = []
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 6
    }
  }, sensors.map(s => {
    const connected = s.connected ?? false;
    return /*#__PURE__*/React.createElement("span", {
      key: s.key,
      title: s.label,
      style: {
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        padding: "2px 6px",
        borderRadius: "var(--radius-sm)",
        fontSize: "var(--text-xs)",
        color: connected ? "var(--text-primary)" : "var(--text-muted)"
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        width: 6,
        height: 6,
        borderRadius: "var(--radius-full)",
        flexShrink: 0,
        background: dotColor(s, s.mock),
        animation: connected && !s.mock && (s.status === "running" || s.status === "normal") ? "kw-pulse-slow 2s var(--ease-standard) infinite" : "none"
      }
    }), s.icon, /*#__PURE__*/React.createElement("span", null, s.label), s.mock && /*#__PURE__*/React.createElement("span", {
      style: {
        padding: "1px 4px",
        fontSize: 9,
        fontWeight: "var(--weight-bold)",
        lineHeight: 1.2,
        borderRadius: "var(--radius-sm)",
        background: "var(--status-simulated)",
        color: "var(--text-inverse)"
      }
    }, "SIM"));
  }));
}
Object.assign(__ds_scope, { SensorStatusBar });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/SensorStatusBar.jsx", error: String((e && e.message) || e) }); }

// components/monitoring/VitalCard.jsx
try { (() => {
function statusOf(value, {
  normalRange,
  warningRange,
  criticalRange,
  status
}) {
  if (typeof value !== "number") return status;
  if (criticalRange && (value < criticalRange.low || value > criticalRange.high)) return "critical";
  if (warningRange && (value < warningRange.low || value > warningRange.high)) return "warning";
  if (normalRange && value >= normalRange.min && value <= normalRange.max) return "normal";
  return status;
}
const CARD_VARIANT = {
  normal: "success",
  warning: "warning",
  alert: "critical",
  critical: "critical"
};
const ICON_STYLE = {
  normal: {
    background: "rgba(22,163,74,.20)",
    color: "var(--status-normal)"
  },
  warning: {
    background: "rgba(250,204,21,.20)",
    color: "var(--status-warning)"
  },
  alert: {
    background: "rgba(239,68,68,.20)",
    color: "var(--status-critical)"
  },
  critical: {
    background: "rgba(239,68,68,.20)",
    color: "var(--status-critical)"
  },
  uncertain: {
    background: "var(--surface-muted)",
    color: "var(--text-muted)"
  }
};
function VitalCard({
  title,
  value,
  unit,
  icon,
  status = "uncertain",
  isLoading,
  normalRange,
  warningRange,
  criticalRange,
  showAsText,
  subtitle
}) {
  const s = statusOf(value, {
    normalRange,
    warningRange,
    criticalRange,
    status
  });
  const valueColor = showAsText ? s === "normal" ? "var(--status-normal)" : "var(--text-muted)" : s === "critical" ? "var(--status-critical)" : s === "warning" ? "var(--status-warning)" : typeof value === "number" && normalRange && value >= normalRange.min && value <= normalRange.max ? "var(--status-normal)" : "var(--text-primary)";
  const display = isLoading || value === null || value === undefined ? "—" : typeof value === "number" ? Math.round(value) : value;
  return /*#__PURE__*/React.createElement(__ds_scope.Card, {
    variant: CARD_VARIANT[s] || "default"
  }, /*#__PURE__*/React.createElement(__ds_scope.CardContent, {
    style: {
      padding: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, title), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      padding: 8,
      borderRadius: "var(--radius-full)",
      ...(ICON_STYLE[s] || ICON_STYLE.uncertain)
    }
  }, icon)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "baseline",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-4xl)",
      fontWeight: "var(--weight-bold)",
      fontVariantNumeric: "tabular-nums",
      letterSpacing: "var(--tracking-tight)",
      color: valueColor,
      opacity: isLoading ? 0.6 : 1
    }
  }, display), unit && !showAsText && /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-lg)",
      color: "var(--text-muted)"
    }
  }, unit)), subtitle ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "4px 0 0",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, subtitle) : normalRange && typeof value === "number" ? /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "8px 0 0",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, "Normal: ", normalRange.min, "\u2013", normalRange.max, " ", unit) : null));
}
Object.assign(__ds_scope, { VitalCard });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/monitoring/VitalCard.jsx", error: String((e && e.message) || e) }); }

// components/onboarding/FeatureItem.jsx
try { (() => {
function FeatureItem({
  icon,
  title,
  description
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flexShrink: 0,
      width: 40,
      height: 40,
      borderRadius: "var(--radius-full)",
      background: "var(--fill-accent)",
      color: "var(--accent-primary)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, icon), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: "var(--text-base)",
      fontWeight: "var(--weight-medium)"
    }
  }, title), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, description)));
}
Object.assign(__ds_scope, { FeatureItem });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/onboarding/FeatureItem.jsx", error: String((e && e.message) || e) }); }

// components/onboarding/NetworkRow.jsx
try { (() => {
function NetworkRow({
  ssid,
  signal = 0,
  secured,
  selected,
  onSelect,
  icon,
  lockIcon
}) {
  const label = signal >= 70 ? "Strong" : signal >= 40 ? "Good" : "Weak";
  return /*#__PURE__*/React.createElement("button", {
    onClick: onSelect,
    style: {
      width: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: 16,
      borderRadius: "var(--radius-lg)",
      cursor: "pointer",
      background: selected ? "var(--fill-accent)" : "var(--surface-card)",
      border: "1px solid " + (selected ? "var(--accent-primary)" : "var(--border-default)"),
      boxShadow: selected ? "0 0 0 2px rgba(124,58,237,.25)" : "none",
      color: "var(--text-primary)",
      fontFamily: "var(--font-body)",
      transition: "all var(--dur-base) var(--ease-standard)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      color: signal >= 70 ? "var(--status-normal)" : signal >= 40 ? "var(--status-warning)" : "var(--text-muted)"
    }
  }, icon), /*#__PURE__*/React.createElement("span", {
    style: {
      textAlign: "left"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontWeight: "var(--weight-medium)"
    }
  }, ssid), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, label, " signal"))), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8,
      color: "var(--text-muted)",
      fontSize: "var(--text-sm)"
    }
  }, secured && lockIcon, /*#__PURE__*/React.createElement("span", {
    style: {
      fontVariantNumeric: "tabular-nums"
    }
  }, signal, "%")));
}
Object.assign(__ds_scope, { NetworkRow });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/onboarding/NetworkRow.jsx", error: String((e && e.message) || e) }); }

// components/onboarding/SensorItem.jsx
try { (() => {
function SensorItem({
  name,
  description,
  detected,
  signal,
  required,
  optional,
  icon
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: 12,
      borderRadius: "var(--radius-lg)",
      border: "1px solid " + (detected ? "rgba(22,163,74,.30)" : "var(--border-default)"),
      background: detected ? "rgba(22,163,74,.05)" : "transparent"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flexShrink: 0,
      width: 40,
      height: 40,
      borderRadius: "var(--radius-full)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      background: detected ? "rgba(22,163,74,.20)" : "var(--surface-muted)",
      color: detected ? "var(--status-normal)" : "var(--text-muted)"
    }
  }, icon), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)"
    }
  }, name), required && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "accent"
  }, "Required"), optional && /*#__PURE__*/React.createElement(__ds_scope.Badge, {
    tone: "neutral"
  }, "Optional")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, description)), detected && signal !== undefined && /*#__PURE__*/React.createElement("div", {
    style: {
      flexShrink: 0,
      textAlign: "right"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)",
      fontVariantNumeric: "tabular-nums"
    }
  }, signal, "%"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, "Signal")));
}
Object.assign(__ds_scope, { SensorItem });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/onboarding/SensorItem.jsx", error: String((e && e.message) || e) }); }

// components/onboarding/StepProgress.jsx
try { (() => {
function StepProgress({
  current = 1,
  total = 6
}) {
  const pct = Math.min(100, Math.max(0, current / total * 100));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: 8,
      borderRadius: "var(--radius-full)",
      background: "var(--surface-muted)",
      overflow: "hidden"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      height: "100%",
      width: pct + "%",
      background: "var(--accent-primary)",
      borderRadius: "var(--radius-full)",
      transition: "width var(--dur-slow) var(--ease-standard)"
    }
  })), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      textAlign: "center",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, "Step ", current, " of ", total));
}
Object.assign(__ds_scope, { StepProgress });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/onboarding/StepProgress.jsx", error: String((e && e.message) || e) }); }

// components/onboarding/TextField.jsx
try { (() => {
function TextField({
  value,
  onChange,
  placeholder,
  type = "text",
  leadingIcon,
  trailingIcon,
  onTrailingClick,
  error,
  disabled
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      position: "relative"
    }
  }, leadingIcon && /*#__PURE__*/React.createElement("span", {
    style: {
      position: "absolute",
      left: 12,
      top: "50%",
      transform: "translateY(-50%)",
      color: "var(--text-muted)",
      display: "inline-flex"
    }
  }, leadingIcon), /*#__PURE__*/React.createElement("input", {
    type: type,
    value: value,
    placeholder: placeholder,
    disabled: disabled,
    onChange: e => onChange && onChange(e.target.value),
    style: {
      width: "100%",
      boxSizing: "border-box",
      padding: `12px ${trailingIcon ? 48 : 12}px 12px ${leadingIcon ? 40 : 12}px`,
      borderRadius: "var(--radius-lg)",
      background: "var(--surface-card)",
      border: "1px solid " + (error ? "var(--red-600)" : "var(--border-default)"),
      color: "var(--text-primary)",
      fontFamily: "var(--font-body)",
      fontSize: "var(--text-base)",
      outline: "none",
      opacity: disabled ? 0.5 : 1
    },
    onFocus: e => {
      e.target.style.borderColor = error ? "var(--red-600)" : "var(--accent-primary)";
      e.target.style.boxShadow = `0 0 0 2px ${error ? "rgba(209,43,43,.5)" : "rgba(124,58,237,.5)"}`;
    },
    onBlur: e => {
      e.target.style.borderColor = error ? "var(--red-600)" : "var(--border-default)";
      e.target.style.boxShadow = "none";
    }
  }), trailingIcon && /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: onTrailingClick,
    disabled: disabled,
    style: {
      position: "absolute",
      right: 12,
      top: "50%",
      transform: "translateY(-50%)",
      border: "none",
      background: "transparent",
      color: "var(--text-muted)",
      cursor: "pointer",
      display: "inline-flex",
      padding: 0
    }
  }, trailingIcon)), error && /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-xs)",
      color: "var(--red-600)"
    }
  }, error));
}
Object.assign(__ds_scope, { TextField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/onboarding/TextField.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/DashboardScreen.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  VitalCard,
  AlertBanner,
  SensorStatusBar,
  AudioLevelMeter,
  EventRow,
  PauseButton,
  StatusIndicator,
  Card,
  CardContent,
  Logo,
  Button
} = window.KnightWatcherDesignSystem_3ee9cb;
function VitalsChart({
  points
}) {
  const w = 1000,
    h = 180;
  const line = (vals, color, min, max, band) => {
    const [lo, hi] = band;
    const d = vals.map((v, i) => `${i === 0 ? "M" : "L"}${i / (vals.length - 1) * w},${h - (lo + (v - min) / (max - min) * (hi - lo)) * h}`).join(" ");
    return /*#__PURE__*/React.createElement("path", {
      d: d,
      fill: "none",
      stroke: color,
      strokeWidth: "2",
      vectorEffect: "non-scaling-stroke"
    });
  };
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 16
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: "var(--text-lg)",
      fontWeight: "var(--weight-medium)"
    }
  }, "Last 30 minutes"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 16,
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 2,
      background: "var(--accent-primary)"
    }
  }), "Respiration"), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 6
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 10,
      height: 2,
      background: "var(--status-normal)"
    }
  }), "Heart rate"))), /*#__PURE__*/React.createElement("svg", {
    viewBox: `0 0 ${w} ${h}`,
    preserveAspectRatio: "none",
    style: {
      width: "100%",
      height: 180,
      display: "block"
    }
  }, [0.25, 0.5, 0.75].map(g => /*#__PURE__*/React.createElement("line", {
    key: g,
    x1: "0",
    x2: w,
    y1: h * g,
    y2: h * g,
    stroke: "var(--border-default)",
    strokeWidth: "1"
  })), line(points.resp, "var(--accent-primary)", 8, 26, [0.06, 0.42]), line(points.hr, "var(--status-normal)", 60, 84, [0.58, 0.94])));
}
function DashboardScreen({
  state,
  onNavigate
}) {
  const {
    vitals,
    alerts,
    paused,
    remaining,
    sensors,
    audioLevel
  } = state;
  return /*#__PURE__*/React.createElement("main", {
    style: {
      minHeight: "100%",
      padding: 32
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      marginBottom: 32,
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(Logo, {
    size: 30
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      borderLeft: "1px solid var(--border-default)",
      paddingLeft: 16
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Last update: 2:16:04 AM")), /*#__PURE__*/React.createElement("div", {
    style: {
      borderLeft: "1px solid var(--border-default)",
      paddingLeft: 16
    }
  }, /*#__PURE__*/React.createElement(SensorStatusBar, {
    sensors: sensors
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(StatusIndicator, {
    status: "online",
    label: "System"
  }), /*#__PURE__*/React.createElement(PauseButton, {
    isPaused: paused,
    remainingMinutes: remaining,
    onPause: state.pause,
    onResume: state.resume,
    pauseIcon: /*#__PURE__*/React.createElement(Icon, {
      name: "Pause",
      size: 16
    }),
    playIcon: /*#__PURE__*/React.createElement(Icon, {
      name: "Play",
      size: 16
    })
  }), /*#__PURE__*/React.createElement("button", {
    onClick: () => onNavigate("settings"),
    title: "Settings",
    style: {
      display: "inline-flex",
      padding: 8,
      borderRadius: "var(--radius-md)",
      border: "none",
      background: "transparent",
      color: "var(--text-muted)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Settings",
    size: 20
  })))), alerts.map(a => /*#__PURE__*/React.createElement("div", {
    key: a.id,
    style: {
      marginBottom: 12
    }
  }, /*#__PURE__*/React.createElement(AlertBanner, _extends({}, a, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: a.level === "critical" ? "XCircle" : "AlertTriangle",
      size: 24
    }),
    onAcknowledge: () => state.acknowledge(a.id),
    onResolve: () => state.resolve(a.id)
  })))), paused && /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 24,
      padding: 16,
      borderRadius: "var(--radius-lg)",
      textAlign: "center",
      background: "rgba(250,204,21,.20)",
      border: "1px solid var(--border-warning)"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      color: "var(--status-warning)",
      fontWeight: "var(--weight-medium)"
    }
  }, "Monitoring paused for ", remaining, " more minutes")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(4, 1fr)",
      gap: 16,
      marginBottom: 32,
      marginTop: alerts.length ? 24 : 0
    }
  }, /*#__PURE__*/React.createElement(VitalCard, {
    title: "Heart Rate",
    value: vitals.hr,
    unit: "BPM",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Heart",
      size: 20
    }),
    status: "normal",
    normalRange: {
      min: 50,
      max: 100
    },
    warningRange: {
      low: 40,
      high: 120
    },
    criticalRange: {
      low: 35,
      high: 150
    }
  }), /*#__PURE__*/React.createElement(VitalCard, {
    title: "Respiration",
    value: vitals.resp,
    unit: "BPM",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Wind",
      size: 20
    }),
    status: "normal",
    normalRange: {
      min: 10,
      max: 25
    },
    warningRange: {
      low: 6,
      high: 30
    },
    criticalRange: {
      low: 4,
      high: 35
    },
    subtitle: "2 sensors \xB7 94% agree"
  }), /*#__PURE__*/React.createElement(VitalCard, {
    title: "Breathing",
    value: vitals.breathing ? "Detected" : "—",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Activity",
      size: 20
    }),
    status: vitals.breathing ? "normal" : "uncertain",
    showAsText: true
  }), /*#__PURE__*/React.createElement(VitalCard, {
    title: "Bed Status",
    value: "Occupied",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Moon",
      size: 20
    }),
    status: "normal",
    showAsText: true
  })), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 24
    }
  }, /*#__PURE__*/React.createElement(VitalsChart, {
    points: state.series
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16
    }
  }, /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement(AudioLevelMeter, {
    level: audioLevel,
    peak: audioLevel + 0.12
  })), /*#__PURE__*/React.createElement(Button, {
    variant: state.listening ? "default" : "secondary",
    size: "sm",
    onClick: state.toggleListen
  }, /*#__PURE__*/React.createElement(Icon, {
    name: state.listening ? "Volume2" : "VolumeX",
    size: 14
  }), state.listening ? "Live" : "Listen"))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(3, 1fr)",
      gap: 16,
      marginTop: 32
    }
  }, [{
    k: "radar",
    c: 0.94
  }, {
    k: "audio",
    c: 0.81
  }, {
    k: "bcg",
    c: null
  }].map(({
    k,
    c
  }) => /*#__PURE__*/React.createElement(Card, {
    key: k
  }, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 16,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)",
      textTransform: "capitalize"
    }
  }, k, " Detector"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Confidence: ", c ? Math.round(c * 100) + "%" : "—")), /*#__PURE__*/React.createElement(StatusIndicator, {
    status: c ? "normal" : "offline"
  }))))), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 32
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: "0 0 12px",
      fontSize: "var(--text-lg)",
      fontWeight: "var(--weight-medium)"
    }
  }, "Last 24 hours"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, state.events.length === 0 ? /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: "center",
      padding: "32px 0",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Activity",
    size: 32,
    style: {
      opacity: 0.5,
      justifyContent: "center"
    }
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "8px 0 0"
    }
  }, "No alerts in the last 24 hours")) : state.events.map(e => /*#__PURE__*/React.createElement(EventRow, _extends({
    key: e.id
  }, e, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: e.level === "critical" ? "XCircle" : "AlertTriangle",
      size: 16
    })
  }))))));
}
Object.assign(window, {
  DashboardScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/DashboardScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/PortalScreen.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
const {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
  Button,
  NetworkRow,
  TextField,
  Logo,
  StatusIndicator
} = window.KnightWatcherDesignSystem_3ee9cb;
const NETWORKS = [{
  ssid: "Home-5G",
  signal: 82,
  secured: true
}, {
  ssid: "Home-2.4G",
  signal: 64,
  secured: true
}, {
  ssid: "Nest-Guest",
  signal: 41,
  secured: true
}, {
  ssid: "xfinitywifi",
  signal: 22,
  secured: false
}];
function PortalScreen() {
  const [step, setStep] = React.useState("connect-hotspot");
  const [ssid, setSsid] = React.useState(null);
  const [password, setPassword] = React.useState("");
  const [show, setShow] = React.useState(false);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 440,
      margin: "0 auto",
      padding: "32px 20px",
      display: "flex",
      flexDirection: "column",
      gap: 20
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Logo, {
    size: 26
  })), step === "connect-hotspot" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, {
    style: {
      paddingBottom: 16
    }
  }, /*#__PURE__*/React.createElement(CardTitle, {
    style: {
      fontSize: "var(--text-lg)",
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 32,
      height: 32,
      borderRadius: "var(--radius-full)",
      background: "var(--fill-accent)",
      color: "var(--accent-primary)",
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-bold)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, "1"), "Connect to KnightWatcher")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      background: "rgba(30,41,59,.5)",
      borderRadius: "var(--radius-lg)",
      padding: 16,
      textAlign: "center"
    }
  }, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "0 0 4px",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)",
      textTransform: "uppercase",
      letterSpacing: "var(--tracking-wider)"
    }
  }, "WiFi Network Name"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-xl)",
      fontWeight: "var(--weight-bold)",
      color: "var(--accent-primary)"
    }
  }, "knightwatcher-a4f1")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, [["Settings", "Open your phone's Settings app"], ["Wifi", "Go to WiFi settings"], ["Smartphone", "Select knightwatcher-a4f1 and connect"]].map(([ic, t]) => /*#__PURE__*/React.createElement("div", {
    key: ic,
    style: {
      display: "flex",
      alignItems: "flex-start",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      flexShrink: 0,
      width: 24,
      height: 24,
      borderRadius: "var(--radius-full)",
      background: "var(--surface-muted)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: ic,
    size: 12
  })), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, t))))), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    style: {
      width: "100%"
    },
    onClick: () => setStep("select-network")
  }, "I'm connected"))), step === "select-network" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, {
    style: {
      fontSize: "var(--text-lg)"
    }
  }, "Choose your home network")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, NETWORKS.map(n => /*#__PURE__*/React.createElement(NetworkRow, _extends({
    key: n.ssid
  }, n, {
    selected: ssid === n.ssid,
    onSelect: () => setSsid(n.ssid),
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: n.signal >= 40 ? "Wifi" : "WifiOff",
      size: 16
    }),
    lockIcon: /*#__PURE__*/React.createElement(Icon, {
      name: "Lock",
      size: 12
    })
  }))), /*#__PURE__*/React.createElement("button", {
    onClick: () => {},
    style: {
      alignSelf: "center",
      marginTop: 4,
      border: "none",
      background: "transparent",
      color: "var(--accent-primary)",
      fontSize: "var(--text-sm)",
      fontFamily: "var(--font-body)",
      cursor: "pointer"
    }
  }, "Scan again")), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    style: {
      width: "100%"
    },
    disabled: !ssid,
    onClick: () => setStep("password")
  }, "Continue"))), step === "password" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, {
    style: {
      fontSize: "var(--text-lg)"
    }
  }, "Password for ", ssid)), /*#__PURE__*/React.createElement(CardContent, null, /*#__PURE__*/React.createElement(TextField, {
    type: show ? "text" : "password",
    value: password,
    onChange: setPassword,
    placeholder: "Enter password",
    leadingIcon: /*#__PURE__*/React.createElement(Icon, {
      name: "Lock",
      size: 16
    }),
    trailingIcon: /*#__PURE__*/React.createElement(Icon, {
      name: show ? "EyeOff" : "Eye",
      size: 16
    }),
    onTrailingClick: () => setShow(!show),
    error: password.length > 0 && password.length < 8 ? "Password must be at least 8 characters" : null
  })), /*#__PURE__*/React.createElement(CardFooter, {
    style: {
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    style: {
      flex: 1
    },
    onClick: () => setStep("select-network")
  }, "Back"), /*#__PURE__*/React.createElement(Button, {
    style: {
      flex: 1
    },
    disabled: password.length < 8,
    onClick: () => setStep("connecting")
  }, "Connect"))), step === "connecting" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 40,
      textAlign: "center",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--accent-primary)",
      animation: "kw-pulse-slow 2s var(--ease-standard) infinite"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Wifi",
    size: 32
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)"
    }
  }, "Joining ", ssid, "\u2026"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "4px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "The hotspot will shut down in 30 seconds")), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm",
    onClick: () => setStep("complete")
  }, "Skip ahead"))), step === "complete" && /*#__PURE__*/React.createElement(Card, {
    variant: "success"
  }, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 32,
      textAlign: "center",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 48,
      height: 48,
      borderRadius: "var(--radius-full)",
      background: "rgba(22,163,74,.20)",
      color: "var(--status-normal)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Check",
    size: 24
  })), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)"
    }
  }, "Connected to ", ssid), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "https://knightwatcher.local"), /*#__PURE__*/React.createElement(StatusIndicator, {
    status: "online",
    label: "Device"
  }), /*#__PURE__*/React.createElement(Button, {
    style: {
      width: "100%",
      marginTop: 8
    },
    onClick: () => setStep("connect-hotspot")
  }, "Open Dashboard"))));
}
Object.assign(window, {
  PortalScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/PortalScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/SettingsScreen.jsx
try { (() => {
const {
  Card,
  CardContent,
  Button,
  Slider,
  StatusIndicator,
  Badge,
  Logo
} = window.KnightWatcherDesignSystem_3ee9cb;
const NAV = [{
  key: "general",
  label: "General",
  icon: "Settings"
}, {
  key: "radar",
  label: "Radar",
  icon: "Radio"
}, {
  key: "audio",
  label: "Audio",
  icon: "Mic"
}, {
  key: "notifications",
  label: "Notifications",
  icon: "Bell"
}, {
  key: "sharing",
  label: "Sharing",
  icon: "Users"
}, {
  key: "alerts",
  label: "Alert Rules",
  icon: "TriangleAlert"
}, {
  key: "updates",
  label: "Updates",
  icon: "Download"
}];
function Row({
  icon,
  title,
  description,
  right
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      padding: 8,
      borderRadius: "var(--radius-full)",
      background: "var(--surface-muted)",
      color: "var(--text-muted)",
      display: "inline-flex"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: icon,
    size: 16
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)"
    }
  }, title), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, description))), right);
}
function SettingsScreen({
  onBack
}) {
  const [tab, setTab] = React.useState("general");
  const [gain, setGain] = React.useState(64);
  const [sensitivity, setSensitivity] = React.useState(70);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      minHeight: "100%"
    }
  }, /*#__PURE__*/React.createElement("header", {
    style: {
      borderBottom: "1px solid var(--border-default)",
      background: "var(--surface-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1024,
      margin: "0 auto",
      padding: "16px 16px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: onBack,
    style: {
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      border: "none",
      background: "transparent",
      color: "var(--text-muted)",
      cursor: "pointer"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "ArrowLeft",
    size: 16
  }), /*#__PURE__*/React.createElement(Logo, {
    variant: "mark",
    size: 22
  })), /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: 0,
      fontSize: "var(--text-xl)",
      fontWeight: "var(--weight-semibold)"
    }
  }, "Settings")))), /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1024,
      margin: "0 auto",
      padding: "24px 16px",
      display: "flex",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("nav", {
    style: {
      width: 192,
      flexShrink: 0
    }
  }, /*#__PURE__*/React.createElement("ul", {
    style: {
      listStyle: "none",
      margin: 0,
      padding: 0,
      display: "flex",
      flexDirection: "column",
      gap: 4
    }
  }, NAV.map(n => /*#__PURE__*/React.createElement("li", {
    key: n.key
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setTab(n.key),
    style: {
      width: "100%",
      display: "flex",
      alignItems: "center",
      gap: 8,
      padding: "8px 12px",
      borderRadius: "var(--radius-md)",
      fontSize: "var(--text-sm)",
      fontFamily: "var(--font-body)",
      cursor: "pointer",
      border: "none",
      textAlign: "left",
      background: tab === n.key ? "var(--surface-muted)" : "transparent",
      color: tab === n.key ? "var(--text-primary)" : "var(--text-muted)",
      fontWeight: tab === n.key ? "var(--weight-medium)" : "var(--weight-regular)"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: n.icon,
    size: 16
  }), n.label))))), /*#__PURE__*/React.createElement("main", {
    style: {
      flex: 1,
      minWidth: 0,
      display: "flex",
      flexDirection: "column",
      gap: 24
    }
  }, tab === "general" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: "0 0 4px",
      fontSize: "var(--text-lg)",
      fontWeight: "var(--weight-semibold)"
    }
  }, "General Settings"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "System status and device information")), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 24
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: "0 0 16px",
      fontWeight: "var(--weight-medium)"
    }
  }, "System Status"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(Row, {
    icon: "Wifi",
    title: "Connection",
    description: "Backend status",
    right: /*#__PURE__*/React.createElement(Badge, {
      tone: "normal"
    }, "online")
  }), /*#__PURE__*/React.createElement(Row, {
    icon: "Clock",
    title: "Last Update",
    description: "Most recent data received",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: "var(--text-sm)",
        color: "var(--text-muted)"
      }
    }, "Just now")
  }), /*#__PURE__*/React.createElement(Row, {
    icon: "HardDrive",
    title: "Detectors",
    description: "Active sensor count",
    right: /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: "var(--text-sm)",
        color: "var(--text-muted)"
      }
    }, "3 active")
  })))), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 24
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: "0 0 16px",
      fontWeight: "var(--weight-medium)"
    }
  }, "Detector Status"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column"
    }
  }, [["radar", "online", "LD2450 on /dev/ttyUSB0"], ["audio", "online", "USB lavalier"], ["bcg", "offline", "No electrode detected"]].map(([n, s, m], i, arr) => /*#__PURE__*/React.createElement("div", {
    key: n,
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "8px 0",
      borderBottom: i < arr.length - 1 ? "1px solid var(--border-default)" : "none"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontWeight: "var(--weight-medium)",
      textTransform: "capitalize"
    }
  }, n), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "2px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, m)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("button", {
    title: `Restart ${n} detector`,
    style: {
      padding: 6,
      borderRadius: "var(--radius-md)",
      border: "none",
      background: "transparent",
      color: "var(--text-muted)",
      cursor: "pointer",
      display: "inline-flex"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "RotateCw",
    size: 16
  })), /*#__PURE__*/React.createElement(Badge, {
    tone: s === "online" ? "normal" : "critical"
  }, s))))))), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      textAlign: "center",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, "KnightWatcher v0.1.0")), tab === "audio" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: "0 0 4px",
      fontSize: "var(--text-lg)",
      fontWeight: "var(--weight-semibold)"
    }
  }, "Audio"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Microphone gain and breathing-sound thresholds")), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 24,
      display: "flex",
      flexDirection: "column",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement(Slider, {
    label: "Microphone gain",
    value: gain,
    onChange: setGain,
    valueLabel: gain + "%"
  }), /*#__PURE__*/React.createElement(Slider, {
    label: "Silence alert threshold",
    value: sensitivity,
    onChange: setSensitivity,
    valueLabel: sensitivity + "%"
  }), /*#__PURE__*/React.createElement(Row, {
    icon: "Mic",
    title: "Live listen",
    description: "Stream device audio to this browser",
    right: /*#__PURE__*/React.createElement(Button, {
      variant: "outline",
      size: "sm"
    }, "Listen")
  })))), tab === "alerts" && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: "0 0 4px",
      fontSize: "var(--text-lg)",
      fontWeight: "var(--weight-semibold)"
    }
  }, "Alert Rules"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Conditions that raise a warning or critical alert")), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 0
    }
  }, [["respiration_low", "radar", "respiration_rate < 8", "15s", "warning"], ["respiration_absent", "radar", "respiration_rate < 4", "10s", "critical"], ["silence", "audio", "no breathing sound", "20s", "critical"]].map(([n, d, c, dur, lvl], i, arr) => /*#__PURE__*/React.createElement("div", {
    key: n,
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: 16,
      borderBottom: i < arr.length - 1 ? "1px solid var(--border-default)" : "none"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-sm)"
    }
  }, n), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "4px 0 0",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, d, " \xB7 ", c, " \xB7 for ", dur)), /*#__PURE__*/React.createElement(Badge, {
    tone: lvl === "critical" ? "critical" : "warning"
  }, lvl)))))), !["general", "audio", "alerts"].includes(tab) && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 40,
      textAlign: "center",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement(StatusIndicator, {
    status: "offline",
    size: "sm"
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "12px 0 0",
      fontSize: "var(--text-sm)"
    }
  }, "The ", NAV.find(n => n.key === tab).label, " panel is not recreated in this kit."))))));
}
Object.assign(window, {
  SettingsScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/SettingsScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/SetupScreen.jsx
try { (() => {
const {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
  Button,
  StepProgress,
  FeatureItem,
  SensorItem,
  TextField,
  Logo,
  Badge
} = window.KnightWatcherDesignSystem_3ee9cb;
const STEPS = ["welcome", "name", "sensors", "notifications", "test", "complete"];
function SetupScreen({
  onExit
}) {
  const [step, setStep] = React.useState(0);
  const [name, setName] = React.useState("");
  const [channels, setChannels] = React.useState({
    sound: true,
    push: false
  });
  const key = STEPS[step];
  const next = () => setStep(s => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep(s => Math.max(s - 1, 0));
  return /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 560,
      margin: "0 auto",
      padding: "40px 24px",
      display: "flex",
      flexDirection: "column",
      gap: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Logo, {
    size: 28
  })), key !== "complete" && /*#__PURE__*/React.createElement(StepProgress, {
    current: step + 1,
    total: STEPS.length
  }), key === "welcome" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, {
    style: {
      textAlign: "center",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement(CardTitle, null, "Welcome to KnightWatcher"), /*#__PURE__*/React.createElement(CardDescription, null, "Let's set up your monitoring system in just a few steps")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "CircleCheck",
      size: 20
    }),
    title: "Non-invasive monitoring",
    description: "No wearables needed \u2014 monitors breathing and movement from a distance"
  }), /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Bell",
      size: 20
    }),
    title: "Instant alerts",
    description: "Get notified immediately if something needs your attention"
  }), /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Lock",
      size: 20
    }),
    title: "Private & secure",
    description: "All data stays on your device \u2014 no cloud required"
  })), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    size: "lg",
    style: {
      width: "100%"
    },
    onClick: next
  }, "Get Started"))), key === "name" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, null, "Who are we watching?"), /*#__PURE__*/React.createElement(CardDescription, null, "This name appears on alerts and in the dashboard")), /*#__PURE__*/React.createElement(CardContent, null, /*#__PURE__*/React.createElement(TextField, {
    value: name,
    onChange: setName,
    placeholder: "Miles",
    leadingIcon: /*#__PURE__*/React.createElement(Icon, {
      name: "User",
      size: 16
    })
  })), /*#__PURE__*/React.createElement(CardFooter, {
    style: {
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    style: {
      flex: 1
    },
    onClick: back
  }, "Back"), /*#__PURE__*/React.createElement(Button, {
    style: {
      flex: 1
    },
    onClick: next,
    disabled: !name.trim()
  }, "Continue"))), key === "sensors" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, null, "Position your sensors"), /*#__PURE__*/React.createElement(CardDescription, null, "Make sure the sensors can see the bed clearly")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(SensorItem, {
    name: "Radar Sensor",
    description: "Detects breathing and movement",
    detected: true,
    signal: 85,
    required: true,
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Check",
      size: 20
    })
  }), /*#__PURE__*/React.createElement(SensorItem, {
    name: "Audio Sensor",
    description: "Listens for breathing sounds",
    detected: true,
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Check",
      size: 20
    })
  }), /*#__PURE__*/React.createElement(SensorItem, {
    name: "BCG Sensor",
    description: "Measures heart rate via mattress",
    optional: true,
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "X",
      size: 20
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      borderRadius: "var(--radius-lg)",
      padding: 16,
      background: "rgba(30,41,59,.5)",
      display: "flex",
      flexDirection: "column",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement("h4", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)"
    }
  }, "Positioning tips:"), /*#__PURE__*/React.createElement("ul", {
    style: {
      margin: 0,
      paddingLeft: 18,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      display: "flex",
      flexDirection: "column",
      gap: 4
    }
  }, /*#__PURE__*/React.createElement("li", null, "Mount radar sensor on wall facing the bed"), /*#__PURE__*/React.createElement("li", null, "Keep 1-2 meters from the bed for best results"), /*#__PURE__*/React.createElement("li", null, "Avoid obstructions between sensor and bed")))), /*#__PURE__*/React.createElement(CardFooter, {
    style: {
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    style: {
      flex: 1
    },
    onClick: back
  }, "Back"), /*#__PURE__*/React.createElement(Button, {
    style: {
      flex: 1
    },
    onClick: next
  }, "Looks Good"))), key === "notifications" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, null, "How should we reach you?"), /*#__PURE__*/React.createElement(CardDescription, null, "Alerts fire the moment a reading leaves its safe range")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, [["sound", "Speaker alarm", "Sounds on the device by the bed"], ["push", "Push notification", "Sent to your phone over your local network"]].map(([k, t, d]) => /*#__PURE__*/React.createElement("button", {
    key: k,
    onClick: () => setChannels(c => ({
      ...c,
      [k]: !c[k]
    })),
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12,
      padding: 16,
      textAlign: "left",
      cursor: "pointer",
      borderRadius: "var(--radius-lg)",
      background: channels[k] ? "var(--fill-accent)" : "var(--surface-card)",
      border: "1px solid " + (channels[k] ? "var(--accent-primary)" : "var(--border-default)"),
      color: "var(--text-primary)",
      fontFamily: "var(--font-body)"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 40,
      height: 40,
      borderRadius: "var(--radius-full)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      background: channels[k] ? "rgba(124,58,237,.25)" : "var(--surface-muted)",
      color: channels[k] ? "var(--accent-primary)" : "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: k === "sound" ? "Volume2" : "Smartphone",
    size: 20
  })), /*#__PURE__*/React.createElement("span", {
    style: {
      flex: 1
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontSize: "var(--text-sm)",
      fontWeight: "var(--weight-medium)"
    }
  }, t), /*#__PURE__*/React.createElement("span", {
    style: {
      display: "block",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, d)), channels[k] && /*#__PURE__*/React.createElement(Icon, {
    name: "Check",
    size: 18,
    style: {
      color: "var(--accent-primary)"
    }
  })))), /*#__PURE__*/React.createElement(CardFooter, {
    style: {
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    style: {
      flex: 1
    },
    onClick: back
  }, "Back"), /*#__PURE__*/React.createElement(Button, {
    style: {
      flex: 1
    },
    onClick: next
  }, "Continue"))), key === "test" && /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardHeader, null, /*#__PURE__*/React.createElement(CardTitle, null, "Test the alarm"), /*#__PURE__*/React.createElement(CardDescription, null, "Play a test alert so you know what to listen for")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: 16,
      borderRadius: "var(--radius-lg)",
      border: "1px solid var(--border-default)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Volume2",
    size: 20,
    style: {
      color: "var(--accent-primary)"
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)"
    }
  }, "Speaker alarm")), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm"
  }, "Play test")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "KnightWatcher is not a medical device. It should supplement, not replace, proper medical supervision.")), /*#__PURE__*/React.createElement(CardFooter, {
    style: {
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    style: {
      flex: 1
    },
    onClick: back
  }, "Back"), /*#__PURE__*/React.createElement(Button, {
    style: {
      flex: 1
    },
    onClick: next
  }, "Finish Setup"))), key === "complete" && /*#__PURE__*/React.createElement(Card, {
    variant: "success"
  }, /*#__PURE__*/React.createElement(CardHeader, {
    style: {
      textAlign: "center",
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 56,
      height: 56,
      borderRadius: "var(--radius-full)",
      background: "rgba(22,163,74,.20)",
      color: "var(--status-normal)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center",
      marginBottom: 8
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Check",
    size: 28
  })), /*#__PURE__*/React.createElement(CardTitle, null, "You're all set"), /*#__PURE__*/React.createElement(CardDescription, null, "KnightWatcher is now watching ", name || "Miles", ". You can change any of this in Settings.")), /*#__PURE__*/React.createElement(CardContent, {
    style: {
      display: "flex",
      justifyContent: "center",
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: "normal"
  }, "Radar online"), /*#__PURE__*/React.createElement(Badge, {
    tone: "normal"
  }, "Audio online"), /*#__PURE__*/React.createElement(Badge, {
    tone: "neutral"
  }, "BCG not connected")), /*#__PURE__*/React.createElement(CardFooter, null, /*#__PURE__*/React.createElement(Button, {
    size: "lg",
    style: {
      width: "100%"
    },
    onClick: onExit
  }, "Open Dashboard"))));
}
Object.assign(window, {
  SetupScreen
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/SetupScreen.jsx", error: String((e && e.message) || e) }); }

// ui_kits/dashboard/icon.jsx
try { (() => {
function Icon({
  name,
  size = 16,
  color,
  style
}) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!ref.current || !window.lucide || !lucide[name]) return;
    ref.current.innerHTML = lucide.createElement(lucide[name]).outerHTML;
    const svg = ref.current.querySelector("svg");
    if (svg) {
      svg.setAttribute("width", size);
      svg.setAttribute("height", size);
    }
  }, [name, size]);
  return /*#__PURE__*/React.createElement("span", {
    ref: ref,
    style: {
      display: "inline-flex",
      color,
      ...style
    }
  });
}
Object.assign(window, {
  Icon
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/dashboard/icon.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing/LandingPage.jsx
try { (() => {
const {
  Logo,
  Button,
  Card,
  CardContent,
  Badge,
  FeatureItem,
  VitalCard,
  StatusIndicator
} = window.KnightWatcherDesignSystem_3ee9cb;
function Nav() {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: "sticky",
      top: 0,
      zIndex: 10,
      borderBottom: "1px solid var(--border-default)",
      background: "rgba(2,8,23,.8)",
      backdropFilter: "blur(8px)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "16px 24px",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement(Logo, {
    size: 26
  }), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 24,
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, /*#__PURE__*/React.createElement("a", {
    href: "#how"
  }, "How it works"), /*#__PURE__*/React.createElement("a", {
    href: "#sensors"
  }, "Sensors"), /*#__PURE__*/React.createElement("a", {
    href: "#build"
  }, "Build one"), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "sm"
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "Github",
    size: 14
  }), "GitHub"))));
}
function Hero() {
  return /*#__PURE__*/React.createElement("section", {
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "80px 24px 64px",
      display: "grid",
      gridTemplateColumns: "1.05fr .95fr",
      gap: 56,
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Badge, {
    tone: "accent"
  }, "Open source \xB7 MIT"), /*#__PURE__*/React.createElement("h1", {
    style: {
      margin: "16px 0 0",
      fontSize: 56,
      lineHeight: 1.05,
      letterSpacing: "var(--tracking-tight)",
      fontWeight: "var(--weight-bold)"
    }
  }, "Non-contact seizure monitoring for the room you can't sit in all night"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "20px 0 0",
      fontSize: "var(--text-lg)",
      lineHeight: "var(--leading-relaxed)",
      color: "var(--text-muted)",
      maxWidth: 520,
      textWrap: "pretty"
    }
  }, "KnightWatcher watches a sleeping child for signs of seizure activity using radar, audio, and bed vibration. Nothing is attached to them, and nothing leaves the house."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12,
      marginTop: 32
    }
  }, /*#__PURE__*/React.createElement(Button, {
    size: "lg"
  }, "Build your own"), /*#__PURE__*/React.createElement(Button, {
    variant: "outline",
    size: "lg"
  }, /*#__PURE__*/React.createElement(Icon, {
    name: "BookOpen",
    size: 16
  }), "Read the docs")), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "20px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Runs on a Raspberry Pi 5. About $123 in parts.")), /*#__PURE__*/React.createElement(Card, null, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 20,
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, "Tonight \xB7 2:16 AM"), /*#__PURE__*/React.createElement(StatusIndicator, {
    status: "online",
    label: "System"
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(VitalCard, {
    title: "Heart Rate",
    value: 72,
    unit: "BPM",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Heart",
      size: 20
    }),
    status: "normal",
    normalRange: {
      min: 50,
      max: 100
    }
  }), /*#__PURE__*/React.createElement(VitalCard, {
    title: "Respiration",
    value: 16,
    unit: "BPM",
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Wind",
      size: 20
    }),
    status: "normal",
    normalRange: {
      min: 10,
      max: 25
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 14,
      borderRadius: "var(--radius-lg)",
      border: "1px solid var(--border-normal)",
      background: "var(--fill-normal)",
      textAlign: "center",
      animation: "kw-breathing-glow 4s var(--ease-standard) infinite"
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: "var(--status-normal)",
      fontWeight: "var(--weight-medium)"
    }
  }, "All clear \u2014 breathing steady")))));
}
function HowItWorks() {
  return /*#__PURE__*/React.createElement("section", {
    id: "how",
    style: {
      borderTop: "1px solid var(--border-default)",
      borderBottom: "1px solid var(--border-default)",
      background: "var(--surface-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "64px 24px",
      display: "grid",
      gridTemplateColumns: "repeat(3,1fr)",
      gap: 32
    }
  }, /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Radio",
      size: 20
    }),
    title: "Non-contact monitoring",
    description: "Nothing is attached to the child. Sensors sit on the wall and the nightstand."
  }), /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Bell",
      size: 20
    }),
    title: "Real-time alerts",
    description: "A speaker alarm by the bed, plus push notifications while you're out."
  }), /*#__PURE__*/React.createElement(FeatureItem, {
    icon: /*#__PURE__*/React.createElement(Icon, {
      name: "Lock",
      size: 20
    }),
    title: "Stays in your house",
    description: "All processing happens on the Pi. Remote access runs over Tailscale \u2014 no cloud service."
  })));
}
const SENSORS = [{
  icon: "Radio",
  name: "Radar",
  detects: "Respiration rate, movement, presence",
  hw: "HLK-LD2450 (24GHz mmWave)",
  status: "Testing soon"
}, {
  icon: "Mic",
  name: "Audio",
  detects: "Breathing sounds, seizure sounds, silence",
  hw: "Lavalier / USB microphone",
  status: "Testing soon"
}, {
  icon: "Activity",
  name: "Capacitive",
  detects: "Heart rate, respiration, bed occupancy",
  hw: "FDC1004 + electrode",
  status: "Planned"
}];
function Sensors() {
  return /*#__PURE__*/React.createElement("section", {
    id: "sensors",
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "72px 24px"
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 36,
      letterSpacing: "var(--tracking-tight)",
      fontWeight: "var(--weight-bold)"
    }
  }, "Three sensors, one picture"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "12px 0 32px",
      color: "var(--text-muted)",
      maxWidth: 620,
      textWrap: "pretty"
    }
  }, "Each detector publishes to an event bus; a fusion engine combines them, so one noisy signal doesn't raise a false alarm on its own."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "grid",
      gridTemplateColumns: "repeat(3,1fr)",
      gap: 16
    }
  }, SENSORS.map(s => /*#__PURE__*/React.createElement(Card, {
    key: s.name
  }, /*#__PURE__*/React.createElement(CardContent, {
    style: {
      padding: 24,
      display: "flex",
      flexDirection: "column",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      width: 40,
      height: 40,
      borderRadius: "var(--radius-full)",
      background: "var(--fill-accent)",
      color: "var(--accent-primary)",
      display: "inline-flex",
      alignItems: "center",
      justifyContent: "center"
    }
  }, /*#__PURE__*/React.createElement(Icon, {
    name: s.icon,
    size: 20
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    style: {
      margin: 0,
      fontSize: "var(--text-xl)",
      fontWeight: "var(--weight-semibold)"
    }
  }, s.name), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "6px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)"
    }
  }, s.detects)), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: 0,
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-xs)",
      color: "var(--text-muted)"
    }
  }, s.hw), /*#__PURE__*/React.createElement(Badge, {
    tone: "neutral"
  }, s.status))))));
}
function Build() {
  return /*#__PURE__*/React.createElement("section", {
    id: "build",
    style: {
      borderTop: "1px solid var(--border-default)",
      background: "var(--surface-card)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "64px 24px",
      display: "grid",
      gridTemplateColumns: "1fr 1fr",
      gap: 48,
      alignItems: "center"
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h2", {
    style: {
      margin: 0,
      fontSize: 36,
      letterSpacing: "var(--tracking-tight)",
      fontWeight: "var(--weight-bold)"
    }
  }, "Build one this weekend"), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "12px 0 24px",
      color: "var(--text-muted)",
      textWrap: "pretty"
    }
  }, "Clone the repo, install the Python package, and run it with mock sensors before any hardware arrives. Enclosure STLs and a full shopping list are in the repo."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Button, null, /*#__PURE__*/React.createElement(Icon, {
    name: "Github",
    size: 16
  }), "Clone the repo"), /*#__PURE__*/React.createElement(Button, {
    variant: "outline"
  }, "Shopping list"))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: 20,
      borderRadius: "var(--radius-lg)",
      border: "1px solid var(--border-default)",
      background: "var(--surface-app)",
      fontFamily: "var(--font-mono)",
      fontSize: "var(--text-sm)",
      lineHeight: 1.8
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--text-muted)"
    }
  }, "# install"), /*#__PURE__*/React.createElement("div", null, "pip install -e ."), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--text-muted)",
      marginTop: 8
    }
  }, "# run with mock sensors"), /*#__PURE__*/React.createElement("div", null, "./bin/mock"), /*#__PURE__*/React.createElement("div", {
    style: {
      color: "var(--text-muted)",
      marginTop: 8
    }
  }, "# dashboard"), /*#__PURE__*/React.createElement("div", null, "http://localhost:3000"))));
}
function Footer() {
  return /*#__PURE__*/React.createElement("footer", {
    style: {
      borderTop: "1px solid var(--border-default)"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      maxWidth: 1120,
      margin: "0 auto",
      padding: "40px 24px",
      display: "flex",
      alignItems: "flex-start",
      justifyContent: "space-between",
      gap: 32
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Logo, {
    size: 22
  }), /*#__PURE__*/React.createElement("p", {
    style: {
      margin: "12px 0 0",
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      maxWidth: 460
    }
  }, "KnightWatcher is not a medical device. It should supplement, not replace, proper medical supervision.")), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: "var(--text-sm)",
      color: "var(--text-muted)",
      textAlign: "right",
      lineHeight: 1.9
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("a", {
    href: "#how"
  }, "Docs")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("a", {
    href: "#sensors"
  }, "Sensors")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("a", {
    href: "#build"
  }, "GitHub")), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 12
    }
  }, "MIT License"))));
}
function LandingPage() {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Nav, null), /*#__PURE__*/React.createElement(Hero, null), /*#__PURE__*/React.createElement(HowItWorks, null), /*#__PURE__*/React.createElement(Sensors, null), /*#__PURE__*/React.createElement(Build, null), /*#__PURE__*/React.createElement(Footer, null));
}
Object.assign(window, {
  LandingPage
});
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing/LandingPage.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Logo = __ds_scope.Logo;

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.CardHeader = __ds_scope.CardHeader;

__ds_ns.CardTitle = __ds_scope.CardTitle;

__ds_ns.CardDescription = __ds_scope.CardDescription;

__ds_ns.CardContent = __ds_scope.CardContent;

__ds_ns.CardFooter = __ds_scope.CardFooter;

__ds_ns.Progress = __ds_scope.Progress;

__ds_ns.Slider = __ds_scope.Slider;

__ds_ns.StatusIndicator = __ds_scope.StatusIndicator;

__ds_ns.AlertBanner = __ds_scope.AlertBanner;

__ds_ns.AudioLevelMeter = __ds_scope.AudioLevelMeter;

__ds_ns.EventRow = __ds_scope.EventRow;

__ds_ns.PauseButton = __ds_scope.PauseButton;

__ds_ns.SensorStatusBar = __ds_scope.SensorStatusBar;

__ds_ns.VitalCard = __ds_scope.VitalCard;

__ds_ns.FeatureItem = __ds_scope.FeatureItem;

__ds_ns.NetworkRow = __ds_scope.NetworkRow;

__ds_ns.SensorItem = __ds_scope.SensorItem;

__ds_ns.StepProgress = __ds_scope.StepProgress;

__ds_ns.TextField = __ds_scope.TextField;

})();
