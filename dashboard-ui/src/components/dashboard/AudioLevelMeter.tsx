"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

interface AudioLevelMeterProps {
  level: number; // 0-1
  className?: string;
}

export function AudioLevelMeter({ level, className }: AudioLevelMeterProps) {
  // Track peak level with decay
  const [peak, setPeak] = useState(0);

  useEffect(() => {
    if (level > peak) {
      setPeak(level);
    } else {
      // Decay peak slowly
      const timer = setTimeout(() => {
        setPeak((prev) => Math.max(level, prev * 0.95));
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [level, peak]);

  const percentage = Math.min(100, Math.max(0, level * 100));
  const peakPercentage = Math.min(100, Math.max(0, peak * 100));

  // Determine color based on level
  const getBarColor = () => {
    if (percentage > 70) return "bg-red-500";
    if (percentage > 40) return "bg-yellow-500";
    return "bg-green-500";
  };

  return (
    <div className={cn("space-y-1", className)}>
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Audio Level</span>
        <span className="font-mono text-muted-foreground">
          {percentage.toFixed(0)}%
        </span>
      </div>
      <div className="relative h-3 bg-muted rounded-full overflow-hidden">
        {/* Main level bar */}
        <div
          className={cn(
            "absolute inset-y-0 left-0 rounded-full transition-all duration-75",
            getBarColor()
          )}
          style={{ width: `${percentage}%` }}
        />
        {/* Peak indicator */}
        {peakPercentage > percentage + 2 && (
          <div
            className="absolute inset-y-0 w-0.5 bg-white/70 transition-all duration-150"
            style={{ left: `${peakPercentage}%` }}
          />
        )}
        {/* Tick marks */}
        <div className="absolute inset-0 flex">
          <div className="flex-1 border-r border-background/20" />
          <div className="flex-1 border-r border-background/20" />
          <div className="flex-1 border-r border-background/20" />
          <div className="flex-1" />
        </div>
      </div>
      {/* Scale labels */}
      <div className="flex justify-between text-[10px] text-muted-foreground/60 px-0.5">
        <span>0</span>
        <span>25</span>
        <span>50</span>
        <span>75</span>
        <span>100</span>
      </div>
    </div>
  );
}
