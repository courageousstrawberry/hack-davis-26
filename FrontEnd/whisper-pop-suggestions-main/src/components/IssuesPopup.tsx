import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import { Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "sonner";

const FLASK_URL = "http://localhost:5000";

const CATEGORIES = ["family", "friends", "work", "school", "relationship"] as const;

type Props = {
  open: boolean;
  onClose: () => void;
  emotion: string;
  transcript: string;
};

export function IssuesPopup({ open, onClose, emotion, transcript }: Props) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);

  const toggle = (cat: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  const handleNext = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${FLASK_URL}/generate-suggestions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          emotion,
          transcript,
          categories: Array.from(selected),
          text,
        }),
      });
      const data = await res.json();
      if (!res.ok || data.error) throw new Error(data.error || "Failed to get suggestions");

      onClose();
      navigate({
        to: "/suggestions",
        search: {
          transcript: data.transcript || transcript,
          suggestions: JSON.stringify(data.suggestions || []),
          loading: false,
        },
      });
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to get suggestions");
    } finally {
      setLoading(false);
    }
  };

  const canProceed = selected.size > 0;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && !loading && onClose()}>
      <DialogContent className="max-w-md rounded-3xl border border-border bg-card/90 backdrop-blur-xl p-8 shadow-card duration-700">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold tracking-tight text-foreground">
            Issues
          </DialogTitle>
        </DialogHeader>

        {emotion && (
          <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-primary/10 px-4 py-1.5 text-sm text-primary">
            Detected emotion: <span className="font-semibold capitalize">{emotion}</span>
          </div>
        )}

        <div className="mt-4 flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => toggle(cat)}
              disabled={loading}
              className={`rounded-full border px-4 py-1.5 text-sm font-medium capitalize transition-colors duration-300 ${
                selected.has(cat)
                  ? "border-primary bg-primary text-primary-foreground shadow-glow"
                  : "border-border bg-background text-muted-foreground hover:border-primary/60 hover:text-foreground"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        <div className="mt-5">
          <textarea
            maxLength={50}
            value={text}
            onChange={(e) => setText(e.target.value)}
            disabled={loading}
            placeholder="Describe your issue… (50 chars max)"
            rows={3}
            className="w-full resize-none rounded-2xl border border-border bg-background/70 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 disabled:opacity-50"
          />
          <p className="mt-1 text-right text-xs text-muted-foreground">{text.length}/50</p>
        </div>

        <button
          type="button"
          onClick={handleNext}
          disabled={!canProceed || loading}
          className={`mt-4 w-full rounded-full bg-gradient-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-glow transition hover:opacity-90 disabled:opacity-40 flex items-center justify-center gap-2 ${
            canProceed && !loading ? "animate-bounce-ready" : ""
          }`}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Getting suggestions…
            </>
          ) : (
            "Next"
          )}
        </button>
      </DialogContent>
    </Dialog>
  );
}
