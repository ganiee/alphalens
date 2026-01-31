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
  CompanyInfo,
  NewsArticleSummary,
  TechnicalIndicators,
  FundamentalMetrics,
  SentimentData,
  ProviderAttribution,
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

  const companyInfo = evidence?.company_info;

  return (
    <div className="rounded-lg bg-white p-6 shadow">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-gray-900">{score.ticker}</span>
            <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
              Rank #{score.rank}
            </span>
          </div>
          {companyInfo && (
            <p className="mt-1 text-sm text-gray-600 truncate" title={companyInfo.name}>
              {companyInfo.name}
            </p>
          )}
          {(companyInfo?.sector || companyInfo?.industry || companyInfo?.exchange) && (
            <div className="mt-1 flex flex-wrap gap-1">
              {companyInfo.sector && (
                <span className="rounded bg-blue-50 px-1.5 py-0.5 text-xs text-blue-700">
                  {companyInfo.sector}
                </span>
              )}
              {companyInfo.industry && (
                <span className="rounded bg-purple-50 px-1.5 py-0.5 text-xs text-purple-700">
                  {companyInfo.industry}
                </span>
              )}
              {companyInfo.exchange && (
                <span className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-600">
                  {companyInfo.exchange}
                </span>
              )}
            </div>
          )}
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
          <TechnicalPanel
            data={evidence.technical}
            provider={evidence.attribution?.market_data_provider}
            fetchedAt={evidence.attribution?.market_data_fetched_at}
          />
          <FundamentalsPanel
            data={evidence.fundamental}
            provider={evidence.attribution?.fundamentals_provider}
            fetchedAt={evidence.attribution?.fundamentals_fetched_at}
          />
          <SentimentPanel data={evidence.sentiment} />
          {evidence.news_articles && evidence.news_articles.length > 0 && (
            <NewsPanel
              articles={evidence.news_articles}
              provider={evidence.attribution?.news_provider}
              fetchedAt={evidence.attribution?.news_fetched_at}
            />
          )}
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

// Helper to format time ago
function timeAgo(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days > 1 ? "s" : ""} ago`;
}

// Provider badge component
function ProviderBadge({ provider }: { provider?: string }) {
  if (!provider) return null;

  const getProviderStyle = (p: string) => {
    switch (p.toLowerCase()) {
      case "polygon":
        return "bg-purple-100 text-purple-800";
      case "fmp":
        return "bg-blue-100 text-blue-800";
      case "newsapi":
        return "bg-green-100 text-green-800";
      case "mock":
        return "bg-gray-100 text-gray-600";
      default:
        return "bg-gray-100 text-gray-600";
    }
  };

  return (
    <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${getProviderStyle(provider)}`}>
      {provider}
    </span>
  );
}

// Panel header with provider badge and timestamp
function PanelHeader({
  title,
  provider,
  fetchedAt,
}: {
  title: string;
  provider?: string;
  fetchedAt?: string | null;
}) {
  return (
    <div className="mb-2 flex items-center justify-between">
      <h4 className="text-sm font-medium text-gray-900">{title}</h4>
      <div className="flex items-center gap-2 text-xs">
        <ProviderBadge provider={provider} />
        {fetchedAt && <span className="text-gray-400">{timeAgo(fetchedAt)}</span>}
      </div>
    </div>
  );
}

// Technical indicators panel
function TechnicalPanel({
  data,
  provider,
  fetchedAt,
}: {
  data: TechnicalIndicators;
  provider?: string;
  fetchedAt?: string | null;
}) {
  const formatValue = (key: string, value: number): string => {
    if (key.includes("price") || key.includes("sma")) {
      return `$${value.toFixed(2)}`;
    }
    return value.toFixed(2);
  };

  const indicators = [
    { key: "current_price", label: "Price" },
    { key: "rsi", label: "RSI" },
    { key: "macd", label: "MACD" },
    { key: "macd_signal", label: "MACD Signal" },
    { key: "sma_50", label: "SMA 50" },
    { key: "sma_200", label: "SMA 200" },
    { key: "volume_trend", label: "Volume Trend" },
  ];

  return (
    <div>
      <PanelHeader title="Technical Indicators" provider={provider} fetchedAt={fetchedAt} />
      <div className="grid grid-cols-2 gap-1 text-xs">
        {indicators.map(({ key, label }) => (
          <div key={key} className="flex justify-between">
            <span className="text-gray-500">{label}:</span>
            <span className="text-gray-900">
              {formatValue(key, data[key as keyof TechnicalIndicators] as number)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Fundamentals panel
function FundamentalsPanel({
  data,
  provider,
  fetchedAt,
}: {
  data: FundamentalMetrics;
  provider?: string;
  fetchedAt?: string | null;
}) {
  const formatValue = (key: string, value: number | null): string => {
    if (value === null) return "N/A";
    if (key === "market_cap") {
      return `$${(value / 1e9).toFixed(1)}B`;
    }
    if (key === "profit_margin") {
      return `${(value * 100).toFixed(1)}%`;
    }
    return value.toFixed(2);
  };

  const metrics = [
    { key: "pe_ratio", label: "P/E Ratio" },
    { key: "revenue_growth", label: "Revenue Growth" },
    { key: "profit_margin", label: "Profit Margin" },
    { key: "debt_to_equity", label: "Debt/Equity" },
    { key: "market_cap", label: "Market Cap" },
  ];

  return (
    <div>
      <PanelHeader title="Fundamentals" provider={provider} fetchedAt={fetchedAt} />
      <div className="grid grid-cols-2 gap-1 text-xs">
        {metrics.map(({ key, label }) => (
          <div key={key} className="flex justify-between">
            <span className="text-gray-500">{label}:</span>
            <span className="text-gray-900">
              {formatValue(key, data[key as keyof FundamentalMetrics])}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// Sentiment panel
function SentimentPanel({ data }: { data: SentimentData }) {
  const getSentimentColor = (score: number) => {
    if (score > 0.2) return "text-green-600";
    if (score < -0.2) return "text-red-600";
    return "text-gray-600";
  };

  return (
    <div>
      <h4 className="mb-2 text-sm font-medium text-gray-900">Sentiment Analysis</h4>
      <div className="grid grid-cols-2 gap-1 text-xs">
        <div className="flex justify-between">
          <span className="text-gray-500">Score:</span>
          <span className={`font-medium ${getSentimentColor(data.score)}`}>
            {data.score.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Articles:</span>
          <span className="text-gray-900">{data.article_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Positive:</span>
          <span className="text-green-600">{data.positive_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Negative:</span>
          <span className="text-red-600">{data.negative_count}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Neutral:</span>
          <span className="text-gray-600">{data.neutral_count}</span>
        </div>
      </div>
    </div>
  );
}

// News articles panel
function NewsPanel({
  articles,
  provider,
  fetchedAt,
}: {
  articles: NewsArticleSummary[];
  provider?: string;
  fetchedAt?: string | null;
}) {
  const getSentimentBadge = (label: string | null) => {
    if (!label) return null;
    const styles: Record<string, string> = {
      positive: "bg-green-100 text-green-800",
      negative: "bg-red-100 text-red-800",
      neutral: "bg-gray-100 text-gray-600",
    };
    return (
      <span className={`rounded px-1.5 py-0.5 text-xs ${styles[label] || styles.neutral}`}>
        {label}
      </span>
    );
  };

  return (
    <div>
      <PanelHeader title="Recent News" provider={provider} fetchedAt={fetchedAt} />
      <div className="space-y-2">
        {articles.map((article, idx) => (
          <div key={idx} className="rounded bg-gray-50 p-2 text-xs">
            <div className="flex items-start justify-between gap-2">
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-blue-600 hover:underline line-clamp-2"
              >
                {article.title}
              </a>
              {getSentimentBadge(article.sentiment_label)}
            </div>
            <div className="mt-1 flex items-center gap-2 text-gray-500">
              <span>{article.source}</span>
              <span>-</span>
              <span>{timeAgo(article.published_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Fallback for unavailable data
function DataUnavailable({ message }: { message: string }) {
  return (
    <div className="rounded bg-gray-100 p-3 text-center text-sm text-gray-500">
      {message}
    </div>
  );
}
