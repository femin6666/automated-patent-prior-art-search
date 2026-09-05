"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  CartesianGrid
} from "recharts";
import { SearchSummary, SearchResultItem } from "@/types";

interface DistributionChartProps {
  summary: SearchSummary;
}

export function SimilarityDistributionChart({ summary }: DistributionChartProps) {
  const data = [
    { name: "Low", count: summary.low_similarity, color: "#10b981" },
    { name: "Moderate", count: summary.moderate_similarity, color: "#f59e0b" },
    { name: "High", count: summary.high_similarity, color: "#f97316" },
    { name: "Very High", count: summary.very_high_similarity, color: "#f43f5e" },
  ];

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
          <XAxis dataKey="name" stroke="#71717a" fontSize={11} tickLine={false} />
          <YAxis stroke="#71717a" fontSize={11} tickLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: "#0d0e15",
              borderColor: "rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#f4f4f5",
              fontSize: "12px",
              boxShadow: "0 10px 25px rgba(0,0,0,0.6)"
            }}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

interface Top5ChartProps {
  results: SearchResultItem[];
}

export function Top5SimilarityChart({ results }: Top5ChartProps) {
  const top5Data = results.slice(0, 5).map((r) => ({
    name: r.patent.title.length > 25 ? r.patent.title.substring(0, 25) + "..." : r.patent.title,
    score: r.final_score,
  }));

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={top5Data}
          margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
          <XAxis type="number" domain={[0, 100]} stroke="#71717a" fontSize={11} unit="%" />
          <YAxis type="category" dataKey="name" stroke="#71717a" fontSize={11} width={130} />
          <Tooltip
            contentStyle={{
              background: "#0d0e15",
              borderColor: "rgba(255, 255, 255, 0.1)",
              borderRadius: "8px",
              color: "#f4f4f5",
              fontSize: "12px",
              boxShadow: "0 10px 25px rgba(0,0,0,0.6)"
            }}
            formatter={(value: any) => [`${value}%`, "Hybrid Score"]}
          />
          <Bar dataKey="score" fill="#6366f1" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
