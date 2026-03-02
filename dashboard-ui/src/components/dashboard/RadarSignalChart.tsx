"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { useQuery } from "convex/react";
import { api } from "../../../convex/_generated/api";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import "chartjs-adapter-date-fns";
import { cn } from "@/lib/utils";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
);

interface RadarSignal {
  _id: string;
  _creationTime: number;
  timestamp: number;
  x: number;
  y: number;
  distance: number;
}

interface RadarSignalChartProps {
  seconds?: number;
  showSmoothed?: boolean;
  className?: string;
}

// Moving average smoothing
function smoothData(data: number[], windowSize: number): number[] {
  if (data.length < windowSize) return data;

  const result: number[] = [];
  let sum = 0;

  // Initialize window
  for (let i = 0; i < windowSize; i++) {
    sum += data[i];
  }
  result.push(sum / windowSize);

  // Slide window
  for (let i = windowSize; i < data.length; i++) {
    sum = sum - data[i - windowSize] + data[i];
    result.push(sum / windowSize);
  }

  // Pad start to match original length
  const padding = Array(data.length - result.length).fill(result[0]);
  return [...padding, ...result];
}

export function RadarSignalChart({
  seconds = 30,
  showSmoothed = true,
  className,
}: RadarSignalChartProps) {
  const [timeRange, setTimeRange] = useState(seconds);
  const chartRef = useRef<ChartJS<"line">>(null);

  // Query radar signal data from Convex
  const signalData = useQuery(api.vitals.getRadarSignal, {
    seconds: timeRange,
    maxPoints: 500,
  });

  // Process data for charting
  const chartData = useMemo(() => {
    if (!signalData || signalData.length === 0) {
      return { datasets: [] };
    }

    const data = signalData as RadarSignal[];

    // Extract Y values and timestamps
    const timestamps = data.map((s: RadarSignal) => s.timestamp);
    const yValues = data.map((s: RadarSignal) => s.y);

    // Calculate baseline (mean)
    const mean = yValues.reduce((a: number, b: number) => a + b, 0) / yValues.length;

    // Calculate deviation from mean (for breathing visualization)
    const deviations = yValues.map((y: number) => y - mean);

    // Smooth the deviations
    const smoothedDeviations = smoothData(deviations, 5);

    const datasets = [
      {
        label: "Raw Signal (Y deviation)",
        data: timestamps.map((t: number, i: number) => ({ x: t, y: deviations[i] })),
        borderColor: "rgba(59, 130, 246, 0.4)",
        backgroundColor: "transparent",
        fill: false,
        tension: 0.1,
        pointRadius: 0,
        borderWidth: 1,
        yAxisID: "y",
      },
    ];

    if (showSmoothed) {
      datasets.push({
        label: "Smoothed Signal",
        data: timestamps.map((t: number, i: number) => ({ x: t, y: smoothedDeviations[i] })),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        yAxisID: "y",
      });
    }

    return { datasets };
  }, [signalData, showSmoothed]);

  // Calculate stats
  const stats = useMemo(() => {
    if (!signalData || signalData.length === 0) {
      return { sampleRate: 0, stdDev: 0, distance: 0 };
    }

    const data = signalData as RadarSignal[];
    const yValues = data.map((s: RadarSignal) => s.y);
    const mean = yValues.reduce((a: number, b: number) => a + b, 0) / yValues.length;
    const variance =
      yValues.reduce((sum: number, y: number) => sum + Math.pow(y - mean, 2), 0) /
      yValues.length;
    const stdDev = Math.sqrt(variance);

    // Calculate sample rate
    const timeSpan =
      data.length > 1
        ? (data[data.length - 1].timestamp - data[0].timestamp) / 1000
        : 1;
    const sampleRate = data.length / timeSpan;

    // Average distance
    const avgDistance =
      data.reduce((sum: number, s: RadarSignal) => sum + s.distance, 0) / data.length;

    return {
      sampleRate: Math.round(sampleRate * 10) / 10,
      stdDev: Math.round(stdDev * 10) / 10,
      distance: Math.round(avgDistance * 100) / 100,
    };
  }, [signalData]);

  // Calculate fixed time window
  const now = Date.now();
  const windowStart = now - timeRange * 1000;

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 0 } as const,
    interaction: { intersect: false, mode: "index" as const },
    plugins: {
      legend: { display: false },
      tooltip: {
        backgroundColor: "hsl(222.2 84% 4.9%)",
        borderColor: "hsl(217.2 32.6% 17.5%)",
        borderWidth: 1,
        titleColor: "hsl(210 40% 98%)",
        bodyColor: "hsl(215 20.2% 65.1%)",
        callbacks: {
          label: function (ctx: any) {
            const val = ctx.parsed.y;
            if (val === null) return "";
            return `${ctx.dataset.label}: ${val.toFixed(1)} mm`;
          },
        },
      },
    },
    scales: {
      x: {
        type: "time" as const,
        min: windowStart,
        max: now,
        time: {
          unit: timeRange <= 60 ? ("second" as const) : ("minute" as const),
          displayFormats: {
            second: "HH:mm:ss",
            minute: "HH:mm",
          },
        },
        grid: { color: "hsl(217.2 32.6% 17.5%)" },
        ticks: { color: "hsl(215 20.2% 65.1%)", maxTicksLimit: 6 },
      },
      y: {
        type: "linear" as const,
        position: "left" as const,
        grid: { color: "hsl(217.2 32.6% 17.5%)" },
        ticks: { color: "#3b82f6" },
        title: {
          display: true,
          text: "Deviation (mm)",
          color: "hsl(215 20.2% 65.1%)",
        },
      },
    },
  };

  const TIME_RANGES = [
    { label: "10s", seconds: 10 },
    { label: "30s", seconds: 30 },
    { label: "1m", seconds: 60 },
    { label: "5m", seconds: 300 },
  ];

  return (
    <div className={cn("space-y-4", className)}>
      {/* Header with tabs */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h3 className="text-base font-semibold">Radar Signal</h3>
          <p className="text-xs text-muted-foreground">
            Y-position deviation from baseline (breathing pattern)
          </p>
        </div>
        <div className="flex gap-1">
          {TIME_RANGES.map((range) => (
            <button
              key={range.seconds}
              onClick={() => setTimeRange(range.seconds)}
              className={cn(
                "px-3 py-1.5 text-xs rounded transition-colors",
                timeRange === range.seconds
                  ? "bg-muted text-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {range.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      {!signalData || signalData.length === 0 ? (
        <div className="h-[180px] flex items-center justify-center text-muted-foreground border border-dashed border-muted rounded-lg">
          No radar signal data
        </div>
      ) : (
        <div className="h-[180px]">
          <Line ref={chartRef} data={chartData} options={options} />
        </div>
      )}

      {/* Stats bar */}
      <div className="flex gap-6 text-sm text-muted-foreground">
        <span>
          Sample rate:{" "}
          <span className="text-foreground font-medium">
            {stats.sampleRate} Hz
          </span>
        </span>
        <span>
          Std dev:{" "}
          <span className="text-foreground font-medium">{stats.stdDev} mm</span>
        </span>
        <span>
          Distance:{" "}
          <span className="text-foreground font-medium">{stats.distance} m</span>
        </span>
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-4 text-sm text-muted-foreground">
        <span className="flex items-center gap-2">
          <span className="w-4 h-0.5 bg-blue-400/40" />
          Raw
        </span>
        {showSmoothed && (
          <span className="flex items-center gap-2">
            <span className="w-4 h-0.5 bg-[#3b82f6]" />
            Smoothed
          </span>
        )}
      </div>
    </div>
  );
}
