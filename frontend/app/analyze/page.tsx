"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppHeader } from "@/components/app-header";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";
import { analyzeStocks, ApiError } from "@/lib/api";

type Horizon = "1W" | "1M" | "3M" | "6M" | "1Y";

const HORIZONS: { value: Horizon; label: string; proOnly: boolean }[] = [
  { value: "1W", label: "1 Week", proOnly: true },
  { value: "1M", label: "1 Month", proOnly: false },
  { value: "3M", label: "3 Months", proOnly: true },
  { value: "6M", label: "6 Months", proOnly: true },
  { value: "1Y", label: "1 Year", proOnly: true },
];

export default function AnalyzePage() {
  return (
    <ProtectedRoute>
      <AnalyzeContent />
    </ProtectedRoute>
  );
}

function AnalyzeContent() {
  const { idToken } = useAuth();
  const router = useRouter();

  const [tickerInput, setTickerInput] = useState("");
  const [horizon, setHorizon] = useState<Horizon>("1M");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  // Get plan from sessionStorage
  const plan =
    typeof window !== "undefined"
      ? sessionStorage.getItem("selectedPlan") || "free"
      : "free";
  const isPro = plan === "pro";
  const maxTickers = isPro ? 5 : 3;

  const parseTickers = (input: string): string[] => {
    return input
      .toUpperCase()
      .split(/[,\s]+/)
      .map((t) => t.trim())
      .filter((t) => t.length > 0 && t.length <= 5 && /^[A-Z]+$/.test(t));
  };

  const tickers = parseTickers(tickerInput);
  const isValidInput = tickers.length > 0 && tickers.length <= maxTickers;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log("handleSubmit called", { isValidInput, hasIdToken: !!idToken, idTokenLength: idToken?.length });
    if (!isValidInput || !idToken) {
      console.log("handleSubmit: Early return - invalid input or no token");
      if (!idToken) {
        setError("Not authenticated. Please sign in again.");
      }
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      console.log("Calling analyzeStocks with", { tickers, horizon, tokenLength: idToken.length });
      const response = await analyzeStocks(tickers, horizon, idToken);
      router.push(`/results/${response.run_id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError("An unexpected error occurred. Please try again.");
      }
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />

      <main className="mx-auto max-w-2xl px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Run Analysis</h2>
          <p className="text-gray-600">
            Enter stock tickers to analyze and get recommendations
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Ticker Input */}
          <div className="rounded-lg bg-white p-6 shadow">
            <label
              htmlFor="tickers"
              className="mb-2 block text-sm font-medium text-gray-700"
            >
              Stock Tickers
            </label>
            <input
              type="text"
              id="tickers"
              value={tickerInput}
              onChange={(e) => setTickerInput(e.target.value)}
              placeholder="AAPL, MSFT, GOOGL"
              className="w-full rounded-md border border-gray-300 px-4 py-2 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              disabled={isLoading}
            />
            <p className="mt-2 text-sm text-gray-500">
              Enter up to {maxTickers} ticker symbols separated by commas or
              spaces
            </p>
            {tickers.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {tickers.map((ticker) => (
                  <span
                    key={ticker}
                    className="rounded-full bg-blue-100 px-3 py-1 text-sm text-blue-800"
                  >
                    {ticker}
                  </span>
                ))}
                {tickers.length > maxTickers && (
                  <span className="rounded-full bg-red-100 px-3 py-1 text-sm text-red-800">
                    Max {maxTickers} tickers
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Horizon Selector */}
          <div className="rounded-lg bg-white p-6 shadow">
            <label className="mb-2 block text-sm font-medium text-gray-700">
              Investment Horizon
            </label>
            <div className="grid grid-cols-5 gap-2">
              {HORIZONS.map((h) => {
                const isDisabled = h.proOnly && !isPro;
                const isSelected = horizon === h.value;

                return (
                  <button
                    key={h.value}
                    type="button"
                    onClick={() => !isDisabled && setHorizon(h.value)}
                    disabled={isDisabled || isLoading}
                    className={`rounded-md px-3 py-2 text-sm font-medium transition-all ${
                      isSelected
                        ? "bg-blue-600 text-white"
                        : isDisabled
                          ? "cursor-not-allowed bg-gray-100 text-gray-400"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    {h.label}
                    {isDisabled && (
                      <span className="ml-1 text-xs">(Pro)</span>
                    )}
                  </button>
                );
              })}
            </div>
            {!isPro && (
              <p className="mt-2 text-sm text-gray-500">
                Upgrade to Pro to unlock all time horizons
              </p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="rounded-md bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={!isValidInput || isLoading}
            className={`w-full rounded-md px-4 py-3 text-center font-medium transition-all ${
              isValidInput && !isLoading
                ? "bg-blue-600 text-white hover:bg-blue-700"
                : "cursor-not-allowed bg-gray-200 text-gray-400"
            }`}
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                Analyzing...
              </span>
            ) : (
              "Analyze Stocks"
            )}
          </button>
        </form>

        {/* Info Card */}
        <div className="mt-6 rounded-lg bg-blue-50 p-4 text-sm text-blue-800">
          <h4 className="font-medium">How it works:</h4>
          <ul className="mt-2 list-inside list-disc space-y-1">
            <li>Technical analysis: RSI, MACD, SMA indicators</li>
            <li>Fundamental analysis: P/E, growth, margins</li>
            <li>Sentiment analysis: News and market sentiment</li>
            <li>Composite score: 40% technical, 30% fundamental, 30% sentiment</li>
          </ul>
        </div>

        {/* Disclaimer */}
        <div className="mt-4 rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Disclaimer:</strong> AlphaLens is for educational purposes
          only. The information provided does not constitute financial advice.
        </div>
      </main>
    </div>
  );
}
