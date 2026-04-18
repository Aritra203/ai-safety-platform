"use client";

import Link from "next/link";
import { ArrowLeft, Code2, BookOpen, Server, GitBranch } from "lucide-react";

export default function APIPage() {
  return (
    <main className="app-shell grid-bg">
      <div className="mx-auto max-w-4xl px-6 py-20">
        <Link
          href="/"
          className="inline-flex items-center gap-2 mb-8 text-slate-300 hover:text-orange-500 transition"
        >
          <ArrowLeft size={18} />
          Back to Home
        </Link>

        <article className="glass rounded-3xl p-8 md:p-12">
          <h1 className="text-4xl font-black text-white mb-4">SafeGuard API</h1>
          <p className="text-sm text-slate-400 mb-8">RESTful API for content analysis and FIR generation</p>

          <div className="prose prose-slate max-w-none space-y-6 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Getting Started</h2>
              <p>
                The SafeGuard API provides programmatic access to our content analysis, legal mapping, and FIR generation capabilities.
              </p>
              <a href="#" className="text-orange-600 font-semibold hover:underline">
                View Full API Documentation →
              </a>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Core Endpoints</h2>
              <div className="space-y-4">
                <div className="flex gap-3 p-3 rounded-lg bg-slate-50">
                  <Code2 className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">/api/v1/analyze</h3>
                    <p className="text-sm">Analyze text, image, or context for harmful content</p>
                  </div>
                </div>
                <div className="flex gap-3 p-3 rounded-lg bg-slate-50">
                  <Code2 className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">/api/v1/legal-mapping</h3>
                    <p className="text-sm">Map incidents to relevant legal sections</p>
                  </div>
                </div>
                <div className="flex gap-3 p-3 rounded-lg bg-slate-50">
                  <Code2 className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">/api/v1/fir-generate</h3>
                    <p className="text-sm">Generate legally valid FIR reports</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Authentication</h2>
              <p>
                All API requests require authentication using bearer tokens. Include your API key in the Authorization header:
              </p>
              <pre className="bg-slate-900 text-white p-4 rounded-lg overflow-x-auto text-sm">
                {`Authorization: Bearer YOUR_API_KEY`}
              </pre>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Rate Limits</h2>
              <ul className="list-disc pl-6 space-y-2">
                <li>Free tier: 100 requests/hour</li>
                <li>Pro tier: 10,000 requests/hour</li>
                <li>Enterprise: Custom limits available</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Resources</h2>
              <div className="grid grid-cols-2 gap-4 mt-4">
                <a href="#" className="flex items-center gap-2 p-3 rounded-lg border border-slate-300 hover:border-orange-400 transition">
                  <BookOpen size={18} className="text-orange-600" />
                  <span className="font-semibold text-white">Documentation</span>
                </a>
                <a href="#" className="flex items-center gap-2 p-3 rounded-lg border border-slate-300 hover:border-orange-400 transition">
                  <GitBranch size={18} className="text-orange-600" />
                  <span className="font-semibold text-white">Code Examples</span>
                </a>
                <a href="#" className="flex items-center gap-2 p-3 rounded-lg border border-slate-300 hover:border-orange-400 transition">
                  <Server size={18} className="text-orange-600" />
                  <span className="font-semibold text-white">API Playground</span>
                </a>
                <a href="mailto:support@safeguard-ai.com" className="flex items-center gap-2 p-3 rounded-lg border border-slate-300 hover:border-orange-400 transition">
                  <span className="text-lg">📧</span>
                  <span className="font-semibold text-white">Support</span>
                </a>
              </div>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
