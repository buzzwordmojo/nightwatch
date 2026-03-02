"use client";

import { useEffect, useRef, useState } from "react";
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

interface Reading {
  timestamp: number;
  respirationRate?: number;
  heartRate?: number;
  breathingAmplitude?: number;
  signalQuality?: number;
  movement?: number;
}

interface VitalsChartProps {
  data: Reading[];
}

const TIME_RANGES = [
  { label: "1m", minutes: 1 },
  { label: "5m", minutes: 5 },
  { label: "15m", minutes: 15 },
  { label: "30m", minutes: 30 },
  { label: "1h", minutes: 60 },
  { label: "4h", minutes: 240 },
  { label: "8h", minutes: 480 },
];

// Downsample data by averaging readings within time buckets
function downsampleData(data: Reading[], bucketSizeMs: number): Reading[] {
  if (data.length === 0) return [];

  const buckets = new Map<number, Reading[]>();

  // Group readings into buckets
  for (const reading of data) {
    const bucketKey = Math.floor(reading.timestamp / bucketSizeMs) * bucketSizeMs;
    if (!buckets.has(bucketKey)) {
      buckets.set(bucketKey, []);
    }
    buckets.get(bucketKey)!.push(reading);
  }

  // Average each bucket
  const result: Reading[] = [];
  for (const [timestamp, readings] of buckets) {
    const avg: Reading = { timestamp };

    const respRates = readings.filter(r => r.respirationRate != null).map(r => r.respirationRate!);
    if (respRates.length > 0) {
      avg.respirationRate = respRates.reduce((a, b) => a + b, 0) / respRates.length;
    }

    const heartRates = readings.filter(r => r.heartRate != null).map(r => r.heartRate!);
    if (heartRates.length > 0) {
      avg.heartRate = heartRates.reduce((a, b) => a + b, 0) / heartRates.length;
    }

    const amplitudes = readings.filter(r => r.breathingAmplitude != null).map(r => r.breathingAmplitude!);
    if (amplitudes.length > 0) {
      avg.breathingAmplitude = amplitudes.reduce((a, b) => a + b, 0) / amplitudes.length;
    }

    const movements = readings.filter(r => r.movement != null || r.signalQuality != null)
      .map(r => r.movement ?? r.signalQuality!);
    if (movements.length > 0) {
      avg.movement = movements.reduce((a, b) => a + b, 0) / movements.length;
    }

    result.push(avg);
  }

  return result.sort((a, b) => a.timestamp - b.timestamp);
}

export function VitalsChart({ data }: VitalsChartProps) {
  const [timeRange, setTimeRange] = useState(5); // Default to 5 minutes
  const chartRef = useRef<ChartJS<"line">>(null);

  // Filter and optionally downsample data based on selected time range
  const filteredData = (() => {
    if (!data || data.length === 0) return [];
    const now = Date.now();
    const cutoff = now - timeRange * 60 * 1000;
    const rangeData = data.filter((r) => r.timestamp >= cutoff);

    // Downsample for longer time ranges to keep chart performant
    // >15 min: 1 sample per minute
    // >1 hour: 1 sample per 5 minutes
    // >4 hours: 1 sample per 15 minutes
    if (timeRange > 240) {
      return downsampleData(rangeData, 15 * 60 * 1000); // 15-minute buckets
    } else if (timeRange > 60) {
      return downsampleData(rangeData, 5 * 60 * 1000); // 5-minute buckets
    } else if (timeRange > 15) {
      return downsampleData(rangeData, 60 * 1000); // 1-minute buckets
    }
    return rangeData;
  })();

  // Transform data for Chart.js
  const chartData = {
    datasets: [
      {
        label: "Breathing (BPM)",
        data: filteredData.map((r) => ({
          x: r.timestamp,
          y: r.respirationRate ?? null,
        })),
        borderColor: "#3b82f6",
        backgroundColor: "rgba(59, 130, 246, 0.1)",
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        yAxisID: "y",
      },
      {
        label: "Heart Rate (BPM)",
        data: filteredData.map((r) => ({
          x: r.timestamp,
          y: r.heartRate ?? null,
        })),
        borderColor: "#8b5cf6",
        backgroundColor: "rgba(139, 92, 246, 0.1)",
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        yAxisID: "y1",
      },
      {
        label: "Movement",
        data: filteredData.map((r) => ({
          x: r.timestamp,
          y: r.movement ?? r.signalQuality ?? null,
        })),
        borderColor: "#10b981",
        backgroundColor: "rgba(16, 185, 129, 0.1)",
        fill: false,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2,
        yAxisID: "y2",
      },
      {
        label: "Audio Level",
        data: filteredData.map((r) => ({
          x: r.timestamp,
          y: r.breathingAmplitude ?? null,
        })),
        borderColor: "#f59e0b",
        backgroundColor: "rgba(245, 158, 11, 0.15)",
        fill: true,
        tension: 0.2,
        pointRadius: 0,
        borderWidth: 1.5,
        yAxisID: "y2",
      },
    ],
  };

  // Calculate fixed time window based on selected range
  const now = Date.now();
  const windowStart = now - timeRange * 60 * 1000;

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
            const label = ctx.dataset.label;
            const val = ctx.parsed.y;
            if (val === null) return "";
            if (label.includes("Movement"))
              return "Movement: " + (val * 100).toFixed(0) + "%";
            if (label.includes("Audio"))
              return "Audio: " + (val * 100).toFixed(0) + "%";
            return label.split(" ")[0] + ": " + val.toFixed(1) + " BPM";
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
          unit:
            timeRange <= 1
              ? ("second" as const)
              : timeRange >= 60
                ? ("hour" as const)
                : ("minute" as const),
          displayFormats: {
            second: "HH:mm:ss",
            minute: "HH:mm",
            hour: "HH:mm",
          },
        },
        grid: { color: "hsl(217.2 32.6% 17.5%)" },
        ticks: { color: "hsl(215 20.2% 65.1%)", maxTicksLimit: 6 },
      },
      y: {
        type: "linear" as const,
        position: "left" as const,
        min: 0,
        max: 35,
        grid: { color: "hsl(217.2 32.6% 17.5%)" },
        ticks: { color: "#3b82f6", stepSize: 10 },
        title: { display: false },
      },
      y1: {
        type: "linear" as const,
        position: "right" as const,
        min: 40,
        max: 140,
        grid: { drawOnChartArea: false },
        ticks: { color: "#8b5cf6", stepSize: 20 },
        title: { display: false },
      },
      y2: {
        type: "linear" as const,
        position: "right" as const,
        min: 0,
        max: 1,
        display: false,
      },
    },
  };

  if (!data || data.length === 0) {
    return (
      <div className="space-y-4">
        {/* Header with tabs */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <h3 className="text-base font-semibold">Vital Signs</h3>
          <div className="flex gap-1">
            {TIME_RANGES.map((range) => (
              <button
                key={range.minutes}
                onClick={() => setTimeRange(range.minutes)}
                className={cn(
                  "px-3 py-1.5 text-xs rounded transition-colors",
                  timeRange === range.minutes
                    ? "bg-muted text-foreground"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        {/* Empty state */}
        <div className="h-[200px] flex items-center justify-center text-muted-foreground">
          No data available
        </div>

        {/* Legend */}
        <div className="flex justify-center gap-4 text-sm text-muted-foreground flex-wrap">
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
            Breathing
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6]" />
            Heart Rate
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
            Movement
          </span>
          <span className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" />
            Audio
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with tabs */}
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h3 className="text-base font-semibold">Vital Signs</h3>
        <div className="flex gap-1">
          {TIME_RANGES.map((range) => (
            <button
              key={range.minutes}
              onClick={() => setTimeRange(range.minutes)}
              className={cn(
                "px-3 py-1.5 text-xs rounded transition-colors",
                timeRange === range.minutes
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
      <div className="h-[200px]">
        <Line ref={chartRef} data={chartData} options={options} />
      </div>

      {/* Legend */}
      <div className="flex justify-center gap-4 text-sm text-muted-foreground flex-wrap">
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#3b82f6]" />
          Breathing
        </span>
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#8b5cf6]" />
          Heart Rate
        </span>
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#10b981]" />
          Movement
        </span>
        <span className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full bg-[#f59e0b]" />
          Audio
        </span>
      </div>
    </div>
  );
}
