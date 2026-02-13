"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import { format } from "date-fns";

interface Reading {
  timestamp: number;
  respirationRate?: number;
  heartRate?: number;
  breathingAmplitude?: number;
  signalQuality?: number;
}

interface VitalsChartProps {
  data: Reading[];
}

export function VitalsChart({ data }: VitalsChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-muted-foreground">
        No data available
      </div>
    );
  }

  // Format data for recharts
  const chartData = data.map((reading) => ({
    time: reading.timestamp,
    timeLabel: format(new Date(reading.timestamp), "HH:mm:ss"),
    respiration: reading.respirationRate,
    heartRate: reading.heartRate,
    quality: reading.signalQuality ? reading.signalQuality * 100 : undefined,
  }));

  return (
    <div className="h-64 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 0, bottom: 5 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="hsl(var(--border))"
            opacity={0.5}
          />
          <XAxis
            dataKey="timeLabel"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="left"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            domain={[0, "auto"]}
          />
          <YAxis
            yAxisId="right"
            orientation="right"
            stroke="hsl(var(--muted-foreground))"
            fontSize={12}
            tickLine={false}
            domain={[0, 120]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "8px",
            }}
            labelStyle={{ color: "hsl(var(--foreground))" }}
            formatter={(value: number, name: string) => {
              if (name === "quality") return [`${Math.round(value)}%`, "Quality"];
              return [Math.round(value), name === "respiration" ? "Respiration" : "Heart Rate"];
            }}
          />
          <Legend
            wrapperStyle={{ paddingTop: "10px" }}
            formatter={(value) => {
              const labels: Record<string, string> = {
                respiration: "Respiration (BPM)",
                heartRate: "Heart Rate (BPM)",
                quality: "Signal Quality (%)",
              };
              return labels[value] || value;
            }}
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="respiration"
            stroke="hsl(142.1 76.2% 36.3%)"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="heartRate"
            stroke="hsl(0 84.2% 60.2%)"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            yAxisId="left"
            type="monotone"
            dataKey="quality"
            stroke="hsl(217.2 91.2% 59.8%)"
            strokeWidth={1}
            strokeDasharray="5 5"
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
