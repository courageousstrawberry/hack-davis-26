import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const CATEGORIES = ["family", "friends", "work", "school", "relationship"] as const;

type Suggestion = { title: string; detail: string };

type Props = {
  open: boolean;
  onClose: () => void;
  transcript: string;
  suggestions: Suggestion[];
};

export function IssuesPopup({ open, onClose, transcript, suggestions }: Props) {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [text, setText] = useState("");

  const toggle = (cat: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  const handleNext = () => {
    onClose();
    navigate({
      to: "/suggestions",
      search: {
        transcript,
        suggestions: JSON.stringify(suggestions),
        loading: false,
      },
    });
  };

  const canProceed = selected.size > 0;

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-md rounded-3xl border border-border bg-card/90 backdrop-blur-xl p-8 shadow-card duration-700">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold tracking-tight text-foreground">
            Issues
          </DialogTitle>
        </DialogHeader>

        <div className="mt-4 flex flex-wrap gap-2">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => toggle(cat)}
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
            placeholder="Describe your issue… (50 chars max)"
            rows={3}
            className="w-full resize-none rounded-2xl border border-border bg-background/70 px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
          />
          <p className="mt-1 text-right text-xs text-muted-foreground">{text.length}/50</p>
        </div>

        <button
          type="button"
          onClick={handleNext}
          disabled={!canProceed}
          className={`mt-4 w-full rounded-full bg-gradient-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-glow transition hover:opacity-90 disabled:opacity-40 ${
            canProceed ? "animate-bounce-ready" : ""
          }`}
        >
          Next
        </button>
      </DialogContent>
    </Dialog>
  );
}
