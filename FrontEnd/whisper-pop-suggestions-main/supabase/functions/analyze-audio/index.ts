// Handles both audio analysis and text-based suggestion generation
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response(null, { headers: corsHeaders });

  try {
    const body = await req.json();
    const { audio, mimeType, emotion, categories, text, transcript: inputTranscript } = body;

    const LOVABLE_API_KEY = Deno.env.get("LOVABLE_API_KEY");
    if (!LOVABLE_API_KEY) throw new Error("LOVABLE_API_KEY not configured");

    const systemPrompt =
      "You are a supportive, empathetic wellbeing assistant. Return 4-6 specific, actionable, and compassionate suggestions tailored to the user's emotional state and situation. Always respond by calling the provided tool.";

    let messages: unknown[];

    if (audio) {
      // Audio path: transcribe + generate suggestions, optionally using emotion/categories context
      const contextNote = [
        emotion ? `Detected emotion from voice analysis: ${emotion}.` : "",
        categories?.length ? `Issue areas the user selected: ${categories.join(", ")}.` : "",
        text ? `User's additional note: "${text}".` : "",
      ].filter(Boolean).join(" ");

      messages = [
        { role: "system", content: systemPrompt },
        {
          role: "user",
          content: [
            {
              type: "text",
              text: `Listen to this audio. Briefly transcribe it, then return 4-6 helpful, varied suggestions the user could act on based on what was said.${contextNote ? " Additional context: " + contextNote : ""}`,
            },
            {
              type: "input_audio",
              input_audio: { data: audio, format: mimeType?.includes("wav") ? "wav" : "mp3" },
            },
          ],
        },
      ];
    } else {
      // Text path: use emotion + categories + text to generate suggestions (no audio)
      const contextParts: string[] = [];
      if (emotion) contextParts.push(`Detected emotion from voice: ${emotion}`);
      if (categories?.length) contextParts.push(`Issue areas: ${categories.join(", ")}`);
      if (inputTranscript) contextParts.push(`What they said: "${inputTranscript}"`);
      if (text) contextParts.push(`Additional context: "${text}"`);

      messages = [
        { role: "system", content: systemPrompt },
        {
          role: "user",
          content: contextParts.join(". ") + ". Please provide helpful, empathetic suggestions.",
        },
      ];
    }

    const resp = await fetch("https://ai.gateway.lovable.dev/v1/chat/completions", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${LOVABLE_API_KEY}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        model: "google/gemini-2.5-flash",
        messages,
        tools: [
          {
            type: "function",
            function: {
              name: "return_suggestions",
              description: "Return transcription/summary and suggestions",
              parameters: {
                type: "object",
                properties: {
                  transcript: { type: "string" },
                  suggestions: {
                    type: "array",
                    items: {
                      type: "object",
                      properties: {
                        title: { type: "string" },
                        detail: { type: "string" },
                      },
                      required: ["title", "detail"],
                      additionalProperties: false,
                    },
                  },
                },
                required: ["transcript", "suggestions"],
                additionalProperties: false,
              },
            },
          },
        ],
        tool_choice: { type: "function", function: { name: "return_suggestions" } },
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text();
      console.error("AI gateway error:", resp.status, errText);
      if (resp.status === 429) {
        return new Response(JSON.stringify({ error: "Rate limit exceeded. Please try again shortly." }), {
          status: 429, headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      if (resp.status === 402) {
        return new Response(JSON.stringify({ error: "AI credits exhausted. Add credits in workspace settings." }), {
          status: 402, headers: { ...corsHeaders, "Content-Type": "application/json" },
        });
      }
      return new Response(JSON.stringify({ error: "AI gateway error" }), {
        status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const data = await resp.json();
    const toolCall = data.choices?.[0]?.message?.tool_calls?.[0];
    const args = toolCall ? JSON.parse(toolCall.function.arguments) : { transcript: "", suggestions: [] };

    return new Response(JSON.stringify(args), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (e) {
    console.error("analyze-audio error:", e);
    return new Response(JSON.stringify({ error: e instanceof Error ? e.message : "Unknown error" }), {
      status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
