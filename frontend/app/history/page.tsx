"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { ProtectedRoute } from "@/components/protected-route";
import { useAuth } from "@/lib/auth-context";
import { getHistory, ApiError, RecommendationSummary } from "@/lib/api";

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <HistoryContent />
    </ProtectedRoute>
  );
}

function HistoryContent() {
  const { idToken } = useAuth();
  const router = useRouter();

  const [runs, setRuns] = useState<RecommendationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      if (!idToken) return;

      try {
        const data = await getHistory(idToken);
        setRuns(data.runs);
      } catch (err) {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Failed to load history");
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, [idToken]);

  const horizonLabels: Record<string, string> = {
    "1W": "1 Week",
    "1M": "1 Month",
    "3M": "3 Months",
    "6M": "6 Months",
    "1Y": "1 Year",
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <AppHeader />

      <main className="mx-auto max-w-7xl px-4 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Analysis History</h2>
          <p className="text-gray-600">View your past stock analyses</p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-300 border-t-blue-600" />
          </div>
        ) : error ? (
          <div className="rounded-md bg-red-50 p-4 text-red-700">{error}</div>
        ) : runs.length === 0 ? (
          <div className="rounded-lg bg-white p-8 text-center shadow">
            <p className="text-gray-600">No analyses yet.</p>
            <button
              onClick={() => router.push("/analyze")}
              className="mt-4 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
              Run Your First Analysis
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {runs.map((run) => (
              <div
                key={run.run_id}
                onClick={() => router.push(`/results/${run.run_id}`)}
                className="cursor-pointer rounded-lg bg-white p-6 shadow transition-all hover:shadow-md"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-medium text-gray-900">
                        {run.tickers.join(", ")}
                      </span>
                      <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                        {horizonLabels[run.horizon] || run.horizon}
                      </span>
                    </div>
                    <p className="mt-1 text-sm text-gray-500">
                      {new Date(run.created_at).toLocaleString()}
                    </p>
                  </div>
                  {run.top_pick && run.top_score && (
                    <div className="text-right">
                      <p className="text-sm text-gray-500">Top Pick</p>
                      <p className="text-lg font-bold text-gray-900">
                        {run.top_pick}
                      </p>
                      <p className="text-sm text-green-600">
                        Score: {run.top_score.toFixed(0)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Disclaimer */}
        <div className="mt-8 rounded-md bg-yellow-50 p-4 text-sm text-yellow-800">
          <strong>Disclaimer:</strong> AlphaLens is for educational purposes
          only. Past analyses do not guarantee future results.
        </div>
      </main>
    </div>
  );
}
