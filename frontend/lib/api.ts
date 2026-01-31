/**
 * API client for backend communication.
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ScoreBreakdown {
  technical: number;
  fundamental: number;
  sentiment: number;
}

export interface StockScore {
  ticker: string;
  composite_score: number;
  breakdown: ScoreBreakdown;
  rank: number;
  allocation_pct: number;
}

export interface TechnicalIndicators {
  rsi: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  sma_50: number;
  sma_200: number;
  current_price: number;
  volume_trend: number;
}

export interface FundamentalMetrics {
  pe_ratio: number | null;
  revenue_growth: number | null;
  profit_margin: number | null;
  debt_to_equity: number | null;
  market_cap: number | null;
}

export interface SentimentData {
  score: number;
  article_count: number;
  positive_count: number;
  negative_count: number;
  neutral_count: number;
}

export interface NewsArticleSummary {
  title: string;
  source: string;
  published_at: string;
  url: string;
  sentiment_label: string | null;
}

export interface ProviderAttribution {
  market_data_provider: string;
  market_data_fetched_at: string | null;
  fundamentals_provider: string;
  fundamentals_fetched_at: string | null;
  news_provider: string;
  news_fetched_at: string | null;
}

export interface EvidencePacket {
  ticker: string;
  technical: TechnicalIndicators;
  fundamental: FundamentalMetrics;
  sentiment: SentimentData;
  fetched_at: string;
  news_articles: NewsArticleSummary[];
  attribution: ProviderAttribution;
}

export interface RecommendationResult {
  run_id: string;
  user_id: string;
  tickers: string[];
  horizon: string;
  scores: StockScore[];
  evidence: EvidencePacket[];
  created_at: string;
}

export interface RecommendationSummary {
  run_id: string;
  tickers: string[];
  horizon: string;
  top_pick: string | null;
  top_score: number | null;
  created_at: string;
}

export interface AnalyzeResponse {
  run_id: string;
  result: RecommendationResult;
}

export interface HistoryResponse {
  runs: RecommendationSummary[];
  total: number;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiRequest<T>(
  endpoint: string,
  accessToken: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

export async function analyzeStocks(
  tickers: string[],
  horizon: string,
  accessToken: string
): Promise<AnalyzeResponse> {
  return apiRequest<AnalyzeResponse>("/recommendations/analyze", accessToken, {
    method: "POST",
    body: JSON.stringify({ tickers, horizon }),
  });
}

export async function getRecommendation(
  runId: string,
  accessToken: string
): Promise<RecommendationResult> {
  return apiRequest<RecommendationResult>(
    `/recommendations/${runId}`,
    accessToken
  );
}

export async function getHistory(
  accessToken: string,
  limit: number = 50,
  offset: number = 0
): Promise<HistoryResponse> {
  return apiRequest<HistoryResponse>(
    `/recommendations/?limit=${limit}&offset=${offset}`,
    accessToken
  );
}
