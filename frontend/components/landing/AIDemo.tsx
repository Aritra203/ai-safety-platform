"use client";

import { useState } from "react";
import { AlertTriangle, Loader2, Play, Sparkles, Zap } from "lucide-react";

const DEMO_EXAMPLES = [
  {
    text: "I know where you live and I'll make sure you regret this. You better watch your back.",
    risk: "CRITICAL",
    labels: ["threat", "cyberbullying"],
    toxic_tokens: ["regret", "watch your back", "know where you live"],
    laws: ["IPC Section 506", "IT Act Section 66A"],
    confidence: 97,
  },
  {
    text: "tujhe to mein dekhta hoon baad mein, stay out of my way or else.",
    risk: "HIGH",
    labels: ["threat", "hate speech"],
    toxic_tokens: ["dekhta hoon", "stay out", "or else"],
    laws: ["IPC Section 503", "IT Act Section 67"],
    confidence: 89,
  },
  {
    text: "Hey sweetie, you're so mature for your age. Can you keep a secret from your parents?",
    risk: "CRITICAL",
    labels: ["grooming", "child exploitation"],
    toxic_tokens: ["sweetie", "mature for your age", "keep a secret", "from your parents"],
    laws: ["POCSO Act Section 11", "IT Act Section 67B"],
    confidence: 99,
  },
];

const riskColors: Record<string, string> = {
  LOW: "badge-low",
  MEDIUM: "badge-medium",
  HIGH: "badge-high",
  CRITICAL: "badge-critical",
};

export default function AIDemo() {
  const [activeExample, setActiveExample] = useState(0);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<null | (typeof DEMO_EXAMPLES)[number]>(null);

  const runDemo = async () => {
    setAnalyzing(true);
    setResult(null);
    await new Promise((resolve) => setTimeout(resolve, 1500));
    setResult(DEMO_EXAMPLES[activeExample]);
    setAnalyzing(false);
  };

  const current = DEMO_EXAMPLES[activeExample];

  const highlightText = (text: string, tokens: string[]) => {
    let highlighted = text;
    tokens.forEach((token) => {
      highlighted = highlighted.replace(new RegExp(`(${token})`, "gi"), `<mark class=\"toxic-highlight\">$1</mark>`);
    });
    return highlighted;
  };

  return (
    <section id="demo" className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="mb-12 text-center md:mb-16">
          <div className="inline-flex items-center gap-2 rounded-full border border-sky-200 bg-sky-50 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-sky-700">
            <Sparkles size={14} />
            Interactive Demo
          </div>
          <h2 className="mt-6 text-4xl font-black leading-tight tracking-[-0.02em] text-slate-900 md:text-6xl">
            Review exactly how the engine
            <span className="gradient-text-cyan block">flags risky language.</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-slate-600">
            Pick a scenario, run the analysis simulation, and inspect category tags, highlighted tokens, and legal section suggestions.
          </p>
        </div>

        <div className="glass rounded-3xl p-4 md:p-6">
          <div className="grid gap-4 md:grid-cols-[0.92fr,1.08fr]">
            <div className="rounded-2xl border border-slate-200 bg-white/85 p-4 md:p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Choose Scenario</p>
              <div className="mt-3 space-y-2">
                {DEMO_EXAMPLES.map((example, index) => (
                  <button
                    key={index}
                    type="button"
                    onClick={() => {
                      setActiveExample(index);
                      setResult(null);
                    }}
                    className={`w-full rounded-xl border px-3 py-3 text-left text-xs transition ${
                      activeExample === index
                        ? "border-orange-300 bg-orange-50"
                        : "border-slate-200 bg-white hover:border-slate-300"
                    }`}
                  >
                    <span className={`mr-2 inline-block rounded-full px-2 py-1 text-[10px] font-bold ${riskColors[example.risk]}`}>
                      {example.risk}
                    </span>
                    <span className="font-semibold text-slate-700">{example.labels.join(" · ")}</span>
                  </button>
                ))}
              </div>

              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700">
                "{current.text}"
              </div>

              <button
                type="button"
                onClick={runDemo}
                disabled={analyzing}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 px-4 py-3 text-sm font-bold text-white shadow-[0_14px_28px_rgba(249,115,22,0.28)] transition hover:translate-y-[-1px] disabled:cursor-not-allowed disabled:opacity-70"
              >
                {analyzing ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    Running Analysis...
                  </>
                ) : (
                  <>
                    <Play size={15} />
                    Run AI Analysis
                  </>
                )}
              </button>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white/85 p-4 md:p-5">
              {!analyzing && !result && (
                <div className="flex h-full min-h-[320px] flex-col items-center justify-center text-center">
                  <div className="mb-3 rounded-full bg-orange-100 p-3 text-orange-700">
                    <Zap size={20} />
                  </div>
                  <p className="text-base font-semibold text-slate-800">Awaiting simulation input</p>
                  <p className="mt-1 max-w-xs text-sm text-slate-500">
                    Trigger the analysis to render highlights, categories, confidence, and legal suggestions.
                  </p>
                </div>
              )}

              {analyzing && (
                <div className="space-y-3">
                  {["Preprocessing text", "Classifying categories", "Extracting legal mappings", "Compiling risk summary"].map((step, index) => (
                    <div key={step} className="rounded-xl border border-slate-200 bg-white p-3">
                      <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">
                        <Loader2 size={12} className="animate-spin" />
                        {step}
                      </div>
                      <div className="skeleton h-3 w-full" style={{ width: `${96 - index * 11}%` }} />
                    </div>
                  ))}
                </div>
              )}

              {result && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <span className={`rounded-full px-3 py-1.5 text-xs font-black tracking-[0.14em] ${riskColors[result.risk]}`}>
                      {result.risk}
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">{result.confidence}% confidence</span>
                  </div>

                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Highlighted Content</p>
                    <div
                      className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm leading-relaxed text-slate-700"
                      dangerouslySetInnerHTML={{ __html: highlightText(result.text, result.toxic_tokens) }}
                    />
                  </div>

                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Detected Categories</p>
                    <div className="flex flex-wrap gap-2">
                      {result.labels.map((label) => (
                        <span key={label} className="rounded-full border border-orange-200 bg-orange-50 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-orange-700">
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="mb-2 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">Suggested Legal Sections</p>
                    <div className="space-y-1.5">
                      {result.laws.map((law) => (
                        <div key={law} className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                          <AlertTriangle size={13} className="text-orange-600" />
                          {law}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
