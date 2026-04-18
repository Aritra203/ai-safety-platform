"use client";

import Link from "next/link";
import { ArrowLeft, BookOpen, FileText, Users, Zap } from "lucide-react";

export default function DocumentationPage() {
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
          <h1 className="text-4xl font-black text-white mb-4">Documentation</h1>
          <p className="text-sm text-slate-400 mb-8">Complete guides and references for SafeGuard AI</p>

          <div className="prose prose-slate max-w-none space-y-8 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Getting Started</h2>
              <div className="space-y-3">
                <div className="flex gap-3 p-4 rounded-lg bg-orange-50 border border-orange-200">
                  <BookOpen className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Installation Guide</h3>
                    <p className="text-sm mt-1">Step-by-step guide to set up SafeGuard AI on your system</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-orange-50 border border-orange-200">
                  <Zap className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900">Quick Start</h3>
                    <p className="text-sm mt-1">Get up and running in 5 minutes with our quick start guide</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">User Guides</h2>
              <div className="space-y-3">
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Text Analysis Guide</h3>
                    <p className="text-sm mt-1">Analyze text content for harmful signals</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Image Analysis Guide</h3>
                    <p className="text-sm mt-1">Process images and extract text with OCR</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">FIR Generation Guide</h3>
                    <p className="text-sm mt-1">Generate legally valid FIR reports with evidence</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Advanced Topics</h2>
              <div className="space-y-3">
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <Users className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Team Management</h3>
                    <p className="text-sm mt-1">Configure teams, roles, and permissions</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <Users className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Analytics Dashboard</h3>
                    <p className="text-sm mt-1">Track trends, metrics, and case statistics</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Need Help?</h2>
              <p>
                Check our <Link href="/support" className="text-orange-600 font-semibold hover:underline">support page</Link> or 
                contact us at <a href="mailto:support@safeguard-ai.com" className="text-orange-600 font-semibold hover:underline">support@safeguard-ai.com</a>
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
