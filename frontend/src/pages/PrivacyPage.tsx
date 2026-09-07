import { Link } from "react-router-dom";
import { usePageTitle } from "@/utils/usePageTitle";

export default function PrivacyPage() {
  usePageTitle("Privacy Policy");
  return (
    <main className="min-h-screen pb-24">
      {/* Top Bar Header */}
      <header className="border-b border-white/[0.08] py-4 px-6 mb-12">
        <div className="max-w-[960px] mx-auto flex items-center justify-between">
          <Link
            to="/"
            className="font-display text-lg tracking-tight text-paper select-none"
          >
            RESUME<span className="text-stamp">ROAST</span>
          </Link>
          <Link
            to="/"
            className="font-mono text-xs text-tan-dim hover:text-tan transition-colors"
          >
            ← Back to Desk
          </Link>
        </div>
      </header>

      <div className="max-w-[720px] mx-auto px-4 text-left space-y-8">
        <div>
          <p className="section-label mb-2">LEGAL &amp; PRIVACY</p>
          <h1 className="font-display text-3xl sm:text-4xl text-paper tracking-tight mb-3">
            Privacy Policy
          </h1>
          <p className="font-mono text-xs text-tan-dim">
            Last updated:{" "}
            {new Date().toLocaleDateString("en-US", {
              month: "long",
              year: "numeric",
            })}
          </p>
        </div>

        <div className="space-y-6 font-body text-sm text-tan leading-relaxed">
          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              1. Document Processing &amp; Retention
            </h2>
            <p>
              When you upload a resume to Resume Roast, the document is read
              in-memory to extract text solely for generating your score,
              critique, audio voice note, and suggested bullet rewrites. Raw PDF
              and DOCX files are discarded immediately following text
              extraction.
            </p>
            <p className="mt-2 font-mono text-xs text-ember">
              Anonymous roast results and extracted excerpts are stored for
              exactly 7 days to enable share links, after which they are
              permanently and irreversibly purged by our automated retention
              cleaner.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              2. Artificial Intelligence &amp; Model Training
            </h2>
            <p>
              We process resumes via enterprise commercial APIs (Google Gemini
              and Anthropic Claude). Under standard commercial terms:
            </p>
            <ul className="list-disc pl-5 mt-2 space-y-1 text-xs font-mono text-tan-dim">
              <li>
                <strong className="text-paper">
                  Zero Foundation Model Training:
                </strong>{" "}
                Your resume text, work history, and personal achievements are
                NEVER used to train, retrain, or improve public AI foundation
                models.
              </li>
              <li>
                <strong className="text-paper">No Third-Party Brokers:</strong>{" "}
                We never sell, rent, license, or provide your data to
                recruiters, talent brokers, or advertisers.
              </li>
              <li>
                <strong className="text-paper">Automated PII Masking:</strong>{" "}
                Sensitive identifiers such as home addresses and phone numbers
                are stripped during analysis.
              </li>
            </ul>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              3. Public Wall of Shame / Wall of Fame
            </h2>
            <p>
              By default, all uploaded resumes are 100% private and accessible
              only via your confidential roast link. A roast is ONLY submitted
              to the public community Wall if you explicitly click the separate
              opt-in button ("Post to Wall of Shame"). You may request removal
              from the public wall at any time with one click.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              4. Device Fingerprinting &amp; Rate Limiting
            </h2>
            <p>
              To prevent bot abuse and manage free-tier daily usage quotas, we
              generate an anonymous one-way cryptographic hash (SHA-256) of
              standard request headers. This hash cannot be reversed to discover
              your personal identity or IP address.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              5. Payment Security
            </h2>
            <p>
              All payments for Pro passes and subscriptions are handled securely
              through PCI-DSS compliant payment gateways (Razorpay). We never
              handle, view, or store raw debit/credit card numbers, UPI PINs, or
              bank passwords on our servers.
            </p>
          </section>

          <section className="border-t border-white/[0.08] pt-6">
            <h2 className="font-display text-lg text-paper mb-2">
              6. Contact &amp; Immediate Data Deletion
            </h2>
            <p>
              If you wish to request the immediate manual deletion of any roast,
              waitlist email, or account record, email our team at{" "}
              <a
                href="mailto:privacy@resumeroast.app"
                className="text-amber-400 underline"
              >
                privacy@resumeroast.app
              </a>{" "}
              or{" "}
              <a
                href="mailto:support@resumeroast.app"
                className="text-amber-400 underline"
              >
                support@resumeroast.app
              </a>
              . Requests are processed within 24 hours.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
