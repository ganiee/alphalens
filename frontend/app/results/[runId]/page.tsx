"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";
import {
  getRecommendation,
  ApiError,
  RecommendationResult,
  StockScore,
  EvidencePacket,
} from "@/lib/api";

export default function ResultsPage() {
  return (
    <ProtectedRoute>
      <ResultsContent />
    </ProtectedRoute>
  );
}

function ResultsContent() {
  const params = useParams();
  const router = useRouter();
  const { accessToken } = useAuth();
  const runId = params.runId as string;

  const [result, setResult] = useState<RecommendationResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedEvidence, setExpandedEvidence] = useState<string | null>(null);

  useEffect(() => {
    const fetchResult = async () => {
      if (!accessToken || !runId) return;

      try {
        const data = await getRecommendation(runId, accessToken);
        setResult(data);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load recommendation result");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchResult();
  }, [accessToken, runId]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          <p className="mt-4 text-gray-600">Loading results...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="rounded-md bg-red-50 p-6 text-red-700">
            <h2 className="text-lg font-semibold">Error</h2>
            <p className="mt-2">{error}</p>
            <button
              onClick={() => router.push("/dashboard")}
              className="mt-4 rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
            >
              Back to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!result) return null;

  const horizonLabels: Record<string, string> = {
    "1W": "1 Week",
    "1M": "1 Month",
    "3M": "3 Months",
    "6M": "6 Months",
    "1Y": "1 Year",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4">
          <h1 className="text-xl font-bold text-gray-900">AlphaLens</h1>
          <div className="space-x-2">
            <button
              onClick={() => router.push("/analyze")}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700"
            >
              New Analysis
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="rounded-md bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
            >
              Dashboard
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
          <div className="mt-2 flex flex-wrap gap-4 text-sm text-gray-600">
            <span>Horizon: {horizonLabels[result.horizon] || result.horizon}</span>
            <span>Tickers: {result.tickers.join(", ")}</span>
            <span>
              Analyzed: {new Date(result.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        {/* Score Cards */}
        <div className="mb-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {result.scores.map((score) => (
            <ScoreCard
              key={score.ticker}
              score={score}
              evidence={result.evidence.find((e) => e.ticker === score.ticker)}
              isExpanded={expandedEvidence === score.ticker}
              onToggleEvidence={() =>
                setExpandedEvidence(
                  expandedEvidence === score.ticker ? null : score.ticker
                )
              }
            />
          ))}
        </div>

        {/* Allocation Summary */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-semibold text-gray-900">
            Recommended Allocation
          </h3>
          <div className="space-y-3">
            {result.scores.map((score) => (
              <div key={score.ticker} className="flex items-center">
                <span className="w-16 font-medium text-gray-900">
                  {score.ticker}
                </span>
                <div className="flex-1 mx-4">
                  <div className="h-4 rounded-full bg-gray-200">
                    <div
                      className="h-4 rounded-full bg-blue-600"
                      style={{ width: `${score.allocation_pct}%` }}
                    />
                  </div>
                </div>
                <span className="w-16 text-right text-sm text-gray-600">
                  {score.allocation_pct.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Disclaimer:</strong> AlphaLens is for educational purposes
          only. The information provided does not constitute financial advice.
          Always do your own research before making investment decisions.
        </div>
      </main>
    </div>
  );
}

interface ScoreCardProps {
  score: StockScore;
  evidence?: EvidencePacket;
  isExpanded: boolean;
  onToggleEvidence: () => void;
}

function ScoreCard({ score, evidence, isExpanded, onToggleEvidence }: ScoreCardProps) {
  const getScoreColor = (value: number) => {
    if (value >= 70) return "text-green-600";
    if (value >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const getScoreBg = (value: number) => {
    if (value >= 70) return "bg-green-100";
    if (value >= 50) return "bg-yellow-100";
    return "bg-red-100";
  };

  return (
    <div className="rounded-lg bg-white p-6 shadow">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <span className="text-2xl font-bold text-gray-900">{score.ticker}</span>
          <span className="ml-2 rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
            Rank #{score.rank}
          </span>
        </div>
        <div
          className={`rounded-full px-4 py-2 text-2xl font-bold ${getScoreBg(score.composite_score)} ${getScoreColor(score.composite_score)}`}
        >
          {score.composite_score.toFixed(0)}
        </div>
      </div>

      {/* Score Breakdown */}
      <div className="mb-4 space-y-2">
        <ScoreBar label="Technical" value={score.breakdown.technical} />
        <ScoreBar label="Fundamental" value={score.breakdown.fundamental} />
        <ScoreBar label="Sentiment" value={score.breakdown.sentiment} />
      </div>

      {/* Allocation */}
      <div className="mb-4 text-sm text-gray-600">
        Allocation: <span className="font-medium text-gray-900">{score.allocation_pct.toFixed(1)}%</span>
      </div>

      {/* Evidence Toggle */}
      {evidence && (
        <button
          onClick={onToggleEvidence}
          className="w-full rounded-md bg-gray-100 px-3 py-2 text-sm text-gray-700 hover:bg-gray-200"
        >
          {isExpanded ? "Hide Details" : "Show Details"}
        </button>
      )}

      {/* Expanded Evidence */}
      {isExpanded && evidence && (
        <div className="mt-4 space-y-4 border-t pt-4">
          <EvidenceSection title="Technical Indicators" data={evidence.technical} />
          <EvidenceSection title="Fundamentals" data={evidence.fundamental} />
          <EvidenceSection title="Sentiment" data={evidence.sentiment} />
        </div>
      )}
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex items-center text-sm">
      <span className="w-24 text-gray-600">{label}</span>
      <div className="mx-2 h-2 flex-1 rounded-full bg-gray-200">
        <div
          className="h-2 rounded-full bg-blue-600"
          style={{ width: `${value}%` }}
        />
      </div>
      <span className="w-8 text-right text-gray-900">{value.toFixed(0)}</span>
    </div>
  );
}

function EvidenceSection({ title, data }: { title: string; data: object }) {
  const formatValue = (key: string, value: unknown): string => {
    if (value === null || value === undefined) return "N/A";
    if (typeof value === "number") {
      if (key.includes("ratio") || key.includes("growth") || key.includes("margin")) {
        return value.toFixed(2);
      }
      if (key.includes("cap")) {
        return `$${(value / 1e9).toFixed(1)}B`;
      }
      if (key.includes("price") || key.includes("sma")) {
        return `$${value.toFixed(2)}`;
      }
      return value.toFixed(2);
    }
    return String(value);
  };

  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-gray-900">{title}</h4>
      <div className="grid grid-cols-2 gap-1 text-xs">
        {Object.entries(data).map(([key, value]) => (
          <div key={key} className="flex justify-between">
            <span className="text-gray-500">{key.replace(/_/g, " ")}:</span>
            <span className="text-gray-900">{formatValue(key, value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
