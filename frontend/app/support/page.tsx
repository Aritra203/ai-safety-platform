"use client";

import Link from "next/link";
import { ArrowLeft, Mail, Phone, MessageSquare, Clock } from "lucide-react";

export default function SupportPage() {
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
          <h1 className="text-4xl font-black text-white mb-4">Support Center</h1>
          <p className="text-sm text-slate-400 mb-8">We're here to help you succeed with SafeGuard AI</p>

          <div className="prose prose-slate max-w-none space-y-8 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Contact Us</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="flex gap-3 p-4 rounded-lg glass">
                  <Mail className="text-orange-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className="font-bold text-white">Email</h3>
                    <a href="mailto:support@safeguard-ai.com" className="text-orange-600 hover:underline">
                      support@safeguard-ai.com
                    </a>
                    <p className="text-xs text-slate-400 mt-1">Response within 24 hours</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg glass">
                  <Phone className="text-orange-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className="font-bold text-white">Phone</h3>
                    <p className="text-white font-semibold">+91-11-XXXX-XXXX</p>
                    <p className="text-xs text-slate-400 mt-1">Mon-Fri, 9 AM - 6 PM IST</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Support Tiers</h2>
              <div className="space-y-3">
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <Clock className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Free Plan</h3>
                    <p className="text-sm">Email support, 48-hour response time</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <Clock className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Professional</h3>
                    <p className="text-sm">Priority email + phone, 4-hour response time</p>
                  </div>
                </div>
                <div className="flex gap-3 p-4 rounded-lg bg-slate-50">
                  <Clock className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-white">Enterprise</h3>
                    <p className="text-sm">24/7 phone + dedicated account manager</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Common Issues</h2>
              <div className="space-y-3">
                <details className="p-4 rounded-lg bg-slate-50 cursor-pointer">
                  <summary className="font-bold text-white">How do I generate an FIR?</summary>
                  <p className="mt-2 text-sm">Navigate to your dashboard, complete the analysis, and click "Generate FIR." The system will create a legally valid report.</p>
                </details>
                <details className="p-4 rounded-lg bg-slate-50 cursor-pointer">
                  <summary className="font-bold text-white">What languages are supported?</summary>
                  <p className="mt-2 text-sm">English, Hindi, Bengali, Marathi, Gujarati, Hinglish, and other major Indian languages.</p>
                </details>
                <details className="p-4 rounded-lg bg-slate-50 cursor-pointer">
                  <summary className="font-bold text-white">How is my data stored?</summary>
                  <p className="mt-2 text-sm">All data is encrypted at rest and in transit using industry-standard protocols. See our Data Security policy for details.</p>
                </details>
                <details className="p-4 rounded-lg bg-slate-50 cursor-pointer">
                  <summary className="font-bold text-white">Do you offer training?</summary>
                  <p className="mt-2 text-sm">Yes, we provide online training and onboarding support for all organizations. Contact support@safeguard-ai.com to schedule.</p>
                </details>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Resources</h2>
              <div className="flex gap-3">
                <MessageSquare className="text-orange-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-white mb-2">FAQ & Community Forum</p>
                  <Link href="/documentation" className="text-orange-600 hover:underline">
                    Browse documentation →
                  </Link>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Report a Bug</h2>
              <p>
                Found an issue? Report it to <a href="mailto:bugs@safeguard-ai.com" className="text-orange-600 font-semibold hover:underline">bugs@safeguard-ai.com</a> or contact our support team. We appreciate detailed bug reports!
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
