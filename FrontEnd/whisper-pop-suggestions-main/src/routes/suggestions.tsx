import { createFileRoute } from "@tanstack/react-router";
import { Sparkles, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

type Suggestion = { title: string; detail: string };

type SearchParams = {
  transcript?: string;
  suggestions?: string; // JSON string
  loading?: boolean;
};

export const Route = createFileRoute("/suggestions")({
  component: Suggestions,
  validateSearch: (search: Record<string, unknown>): SearchParams => ({
    transcript: (search.transcript as string) || "",
    suggestions: (search.suggestions as string) || "[]",
    loading: (search.loading as boolean) || false,
  }),
});

function Suggestions() {
  const { transcript, suggestions: suggestionsJson, loading } = Route.useSearch();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);

  useEffect(() => {
    try {
      setSuggestions(JSON.parse(suggestionsJson));
    } catch {
      setSuggestions([]);
    }
  }, [suggestionsJson]);

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <div className="max-w-4xl w-full">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs text-muted-foreground backdrop-blur">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            AI-powered audio insights
          </div>
          <h1 className="bg-gradient-primary bg-clip-text text-4xl font-bold tracking-tight text-transparent">
            Your Suggestions
          </h1>
          <p className="mt-2 text-muted-foreground">
            {loading ? "Analyzing your audio…" : transcript ? `"${transcript}"` : "Based on what you said"}
          </p>
        </div>

        <div className="space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12 text-muted-foreground">
              <Loader2 className="mr-2 h-5 w-5 animate-spin" />
              Listening carefully…
            </div>
          ) : suggestions.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="rounded-xl border border-border bg-card p-6 shadow-card hover:shadow-glow transition-shadow"
                >
                  <h3 className="font-semibold text-lg mb-2">{suggestion.title}</h3>
                  <p className="text-muted-foreground text-sm">{suggestion.detail}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-border bg-background/50 p-12 text-center shadow-card">
              <p className="text-muted-foreground">No suggestions available yet.</p>
            </div>
          )}
        </div>

        <div className="mt-8 text-center">
          <button
            onClick={() => window.history.back()}
            className="text-sm text-muted-foreground underline-offset-4 hover:text-primary hover:underline"
          >
            Go back
          </button>
        </div>
      </div>
    </main>
  );
}