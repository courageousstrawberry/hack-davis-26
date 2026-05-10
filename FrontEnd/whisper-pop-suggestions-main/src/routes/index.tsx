import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useRef, useState } from "react";
import { Mic, Square, Upload, Sparkles, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { Toaster } from "@/components/ui/sonner";
import { supabase } from "@/integrations/supabase/client";
import { IssuesPopup } from "@/components/IssuesPopup";

export const Route = createFileRoute("/")({
  component: Index,
});

type Suggestion = { title: string; detail: string };

function Index() {
  const [recording, setRecording] = useState(false);
  const [loading, setLoading] = useState(false);
  const [popupOpen, setPopupOpen] = useState(false);
  const [pendingTranscript, setPendingTranscript] = useState("");
  const [pendingSuggestions, setPendingSuggestions] = useState<Suggestion[]>([]);
  const navigate = useNavigate();

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  const blobToBase64 = (blob: Blob) =>
    new Promise<string>((resolve, reject) => {
      const r = new FileReader();
      r.onloadend = () => {
        const s = (r.result as string).split(",")[1];
        resolve(s);
      };
      r.onerror = reject;
      r.readAsDataURL(blob);
    });

  const sendAudio = async (blob: Blob, mimeType: string) => {
    setLoading(true);
    try {
      const audio = await blobToBase64(blob);
      const { data, error } = await supabase.functions.invoke("analyze-audio", {
        body: { audio, mimeType },
      });
      if (error) throw error;
      if (data?.error) throw new Error(data.error);
      setPendingTranscript(data.transcript || "");
      setPendingSuggestions(data.suggestions || []);
      toast.success("Audio analyzed — click Next Step to continue");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Failed to analyze audio";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => e.data.size > 0 && chunksRef.current.push(e.data);
      mr.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        stream.getTracks().forEach((t) => t.stop());
        await sendAudio(blob, "audio/webm");
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch {
      toast.error("Microphone access denied");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setRecording(false);
  };

  const onUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    await sendAudio(f, f.type || "audio/mpeg");
    e.target.value = "";
  };

  const handleRestart = () => {
    mediaRef.current?.stop();
    mediaRef.current = null;
    chunksRef.current = [];
    setRecording(false);
    setLoading(false);
    setPopupOpen(false);
    setPendingTranscript("");
    setPendingSuggestions([]);
  };

  const handleNextStep = () => {
    setPopupOpen(true);
  };

  return (
    <main className="relative flex min-h-screen flex-col items-center justify-center px-6 py-12">
      <Toaster richColors position="top-center" />
      <div className="max-w-xl text-center">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-4 py-1.5 text-xs text-muted-foreground backdrop-blur">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          AI-powered audio insights
        </div>
        <h1 className="bg-gradient-primary bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-6xl">
          Speak. We Will Listen. You Discover.
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Record or upload an audio clip and get instant suggestions tailored to your emotions.
        </p>

        <div className="mt-12 flex flex-col items-center gap-6">
          <div className="relative">
            {recording && (
              <span className="absolute inset-0 animate-pulse-ring rounded-full bg-primary/40" />
            )}
            <button
              onClick={recording ? stopRecording : startRecording}
              disabled={loading}
              className="relative flex h-28 w-28 items-center justify-center rounded-full bg-gradient-primary text-primary-foreground animate-pop-pulse hover:scale-110 active:scale-95 transition-transform duration-300 disabled:opacity-50"
              aria-label={recording ? "Stop recording" : "Start recording"}
            >
              {loading ? <Loader2 className="h-10 w-10 animate-spin" /> : recording ? <Square className="h-10 w-10" /> : <Mic className="h-10 w-10" />}
            </button>
          </div>
          <p className="text-sm text-muted-foreground">
            {loading ? "Analyzing…" : recording ? "Recording… tap to stop" : pendingSuggestions.length > 0 ? "Audio ready" : "Tap to record"}
          </p>

          <div className="flex items-center gap-3">
            <span className="h-px w-10 bg-border" />
            <span className="text-xs uppercase tracking-wider text-muted-foreground">or</span>
            <span className="h-px w-10 bg-border" />
          </div>

          <label>
            <input type="file" accept="audio/*" className="hidden" onChange={onUpload} disabled={loading} />
            <Button variant="secondary" size="lg" asChild>
              <span className="cursor-pointer">
                <Upload className="mr-2 h-4 w-4" />
                Upload audio file
              </span>
            </Button>
          </label>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleNextStep}
              disabled={loading || recording || pendingSuggestions.length === 0}
              className="inline-flex items-center justify-center rounded-full bg-gradient-primary px-8 py-3 text-sm font-semibold text-primary-foreground shadow-glow transition hover:opacity-90 disabled:opacity-40"
            >
              Next Step
            </button>
            <button
              type="button"
              onClick={handleRestart}
              className="inline-flex items-center justify-center rounded-full border border-border bg-background px-8 py-3 text-sm font-semibold text-foreground transition hover:bg-muted"
            >
              Restart
            </button>
          </div>
          <IssuesPopup
            open={popupOpen}
            onClose={() => setPopupOpen(false)}
            transcript={pendingTranscript}
            suggestions={pendingSuggestions}
          />
        </div>
      </div>
    </main>
  );
}
