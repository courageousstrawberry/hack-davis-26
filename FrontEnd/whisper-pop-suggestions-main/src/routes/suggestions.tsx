import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { motion } from "motion/react";
import { Sparkles, Mail, Star, Loader2 } from "lucide-react";

type Suggestion = { title: string; detail: string };

type SearchParams = {
  transcript?: string;
  suggestions?: string;
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

const BG_CIRCLES = Array.from({ length: 12 }, (_, i) => ({
  id: i,
  width: 60 + ((i * 37) % 100),
  height: 60 + ((i * 53) % 100),
  left: (i * 83) % 100,
  top: (i * 67) % 100,
  color:
    i % 3 === 0
      ? "rgba(86,144,153,0.08)"
      : i % 3 === 1
        ? "rgba(164,218,210,0.12)"
        : "rgba(246,216,9,0.07)",
  dx: ((i * 29) % 100) - 50,
  dy: ((i * 41) % 100) - 50,
  duration: 10 + (i * 7) % 10,
  delay: (i * 13) % 5,
}));

const SPARKLES = Array.from({ length: 8 }, (_, i) => ({
  id: i,
  left: (i * 97) % 100,
  top: (i * 71) % 100,
  duration: 5 + (i * 11) % 5,
  delay: (i * 17) % 5,
  big: i % 2 === 0,
}));

const STARS = Array.from({ length: 15 }, (_, i) => ({
  id: i,
  left: (i * 61) % 100,
  top: (i * 43) % 100,
  duration: 6 + (i * 9) % 8,
  delay: (i * 7) % 3,
  big: i % 2 === 0,
  color:
    i % 3 === 0
      ? "text-primary/40"
      : i % 3 === 1
        ? "text-primary/30"
        : "text-accent/50",
  fill: i % 4 === 0,
}));

function Suggestions() {
  const { transcript, suggestions: suggestionsJson = "[]", loading = false } =
    Route.useSearch();
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isHovered, setIsHovered] = useState(false);

  useEffect(() => {
    try {
      setSuggestions(JSON.parse(suggestionsJson));
    } catch {
      setSuggestions([]);
    }
  }, [suggestionsJson]);

  return (
    <div className="size-full min-h-screen flex items-center justify-center p-8 relative overflow-hidden">
      {/* animated bg circles */}
      {BG_CIRCLES.map((c) => (
        <motion.div
          key={c.id}
          className="absolute rounded-full pointer-events-none"
          style={{
            width: c.width,
            height: c.height,
            background: `radial-gradient(circle, ${c.color}, transparent)`,
            left: `${c.left}%`,
            top: `${c.top}%`,
          }}
          animate={{ x: [0, c.dx, 0], y: [0, c.dy, 0], scale: [1, 1.2, 1], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: c.duration, repeat: Infinity, ease: "easeInOut", delay: c.delay }}
        />
      ))}

      {/* floating sparkles */}
      {SPARKLES.map((s) => (
        <motion.div
          key={`sp-${s.id}`}
          className="absolute pointer-events-none text-primary/50"
          style={{ left: `${s.left}%`, top: `${s.top}%` }}
          animate={{ y: [0, -100, -200], opacity: [0, 1, 0], scale: [0.5, 1, 0.5] }}
          transition={{ duration: s.duration, repeat: Infinity, ease: "easeOut", delay: s.delay }}
        >
          <Sparkles className={s.big ? "w-4 h-4" : "w-3 h-3"} />
        </motion.div>
      ))}

      {/* stars */}
      {STARS.map((s) => (
        <motion.div
          key={`st-${s.id}`}
          className="absolute pointer-events-none"
          style={{ left: `${s.left}%`, top: `${s.top}%` }}
          animate={{ rotate: [0, 360], opacity: [0.2, 0.8, 0.2], scale: [0.8, 1.2, 0.8] }}
          transition={{ duration: s.duration, repeat: Infinity, ease: "easeInOut", delay: s.delay }}
        >
          <Star className={`${s.big ? "w-4 h-4" : "w-3 h-3"} ${s.color} ${s.fill ? "fill-current" : ""}`} />
        </motion.div>
      ))}

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
        className="w-full max-w-2xl relative z-10"
      >
        <div
          className="relative bg-card/90 backdrop-blur-sm rounded-3xl shadow-card overflow-hidden border border-border"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          <motion.div
            className="absolute inset-0 bg-gradient-to-br from-primary/10 via-primary-glow/10 to-accent/10"
            animate={{ opacity: isHovered ? 1 : 0.5 }}
            transition={{ duration: 0.8 }}
          />

          <div className="relative p-12">
            {/* icon */}
            <div className="flex items-center justify-center mb-8">
              <motion.div
                animate={{ rotate: [0, 5, -5, 0], y: [0, -5, 0] }}
                transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                className="bg-gradient-primary p-4 rounded-full shadow-glow"
              >
                <Sparkles className="w-8 h-8 text-primary-foreground" />
              </motion.div>
            </div>

            {/* floating content card */}
            <div className="relative min-h-[200px] flex items-center justify-center">
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: [0, -10, 0] }}
                transition={{ opacity: { duration: 1.5 }, y: { duration: 4, repeat: Infinity, ease: "easeInOut" } }}
                className="relative w-full bg-gradient-to-br from-primary/10 to-primary-glow/20 backdrop-blur-md rounded-2xl p-8 shadow-card border border-border"
              >
                <h1 className="text-center text-2xl font-semibold bg-gradient-primary bg-clip-text text-transparent mb-2">
                  Your Suggestions
                </h1>

                {transcript && (
                  <p className="text-center text-sm text-muted-foreground mb-6">"{transcript}"</p>
                )}

                {loading ? (
                  <div className="flex flex-col items-center gap-3 py-6 text-primary">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <span className="text-sm font-light">Listening carefully…</span>
                  </div>
                ) : suggestions.length > 0 ? (
                  <div className="grid gap-3 sm:grid-cols-2 mt-4">
                    {suggestions.map((s, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 16 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + i * 0.15, duration: 0.6 }}
                        className="rounded-2xl border border-border bg-card/80 p-4 shadow-card hover:shadow-glow transition-shadow"
                      >
                        <h3 className="text-sm font-semibold text-foreground mb-1">{s.title}</h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">{s.detail}</p>
                      </motion.div>
                    ))}
                  </div>
                ) : (
                  <p className="text-center text-sm text-muted-foreground mt-4">
                    No suggestions available yet.
                  </p>
                )}

                {/* animated dots */}
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 1, delay: 1.5 }}
                  className="flex items-center justify-center gap-2 mt-6"
                >
                  {[...Array(5)].map((_, i) => (
                    <motion.div
                      key={i}
                      animate={{ opacity: [0.3, 1, 0.3], scale: [1, 1.2, 1] }}
                      transition={{ duration: 3, delay: i * 0.3, repeat: Infinity, ease: "easeInOut" }}
                      className="w-1.5 h-1.5 rounded-full bg-primary/50"
                    />
                  ))}
                </motion.div>

                {/* corner sparkles */}
                <motion.div
                  className="absolute -top-4 -right-4"
                  animate={{ rotate: 360, scale: [1, 1.1, 1] }}
                  transition={{ rotate: { duration: 20, repeat: Infinity, ease: "linear" }, scale: { duration: 2, repeat: Infinity, ease: "easeInOut" } }}
                >
                  <Sparkles className="w-6 h-6 text-primary/40" />
                </motion.div>
                <motion.div
                  className="absolute -bottom-6 -left-6"
                  animate={{ rotate: -360, scale: [1, 1.2, 1] }}
                  transition={{ rotate: { duration: 25, repeat: Infinity, ease: "linear" }, scale: { duration: 3, repeat: Infinity, ease: "easeInOut" } }}
                >
                  <Sparkles className="w-5 h-5 text-primary-glow/60" />
                </motion.div>
              </motion.div>
            </div>

            {/* buttons */}
            <div className="flex items-center justify-center gap-4 mt-8">
              <motion.button
                type="button"
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => window.history.back()}
                className="bg-gradient-to-r from-destructive to-orange-500 text-destructive-foreground px-6 py-3.5 rounded-full font-medium shadow-glow hover:opacity-90 transition-all duration-300"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2, duration: 1 }}
              >
                Call 988 for emergency
              </motion.button>

              <motion.button
                type="button"
                whileHover={{ scale: 1.05, y: -2 }}
                whileTap={{ scale: 0.95 }}
                className="bg-gradient-to-r from-secondary to-emerald-500 text-secondary-foreground px-10 py-3.5 rounded-full font-medium flex items-center gap-3 shadow-card hover:shadow-glow transition-all duration-300"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2, duration: 1 }}
              >
                <Mail className="w-5 h-5" />
                Email
              </motion.button>
            </div>
          </div>

          {/* bottom gradient bar */}
          <motion.div
            className="h-1 bg-gradient-primary"
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 2, delay: 0.5 }}
            style={{ transformOrigin: "left" }}
          />
        </div>
      </motion.div>
    </div>
  );
}
