import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { analyzeService } from "@/services/analyzeService";
import { RiskBadge } from "@/components/common/RiskBadge";
import { ScoreRing } from "@/components/common/ScoreRing";

export function AnalyzePage() {
  const [text, setText] = useState("");
  const [channel, setChannel] = useState("other");
  const [url, setUrl] = useState("");
  const analysis = useMutation({ mutationFn: () => analyzeService.text(text.trim(), channel) });
  const urlAnalysis = useMutation({ mutationFn: () => analyzeService.url(url.trim()) });
  return <div className="page-stack">
    <div className="page-header"><div><span className="eyebrow">Connected backend</span><h1>Analyze a message or link.</h1><p>Use the existing API without submitting content for storage.</p></div></div>
    <p className="empty-period-note">No AI required. Messages are compared with stored scam examples using word overlap and sequence matching (72% threshold). Similarity is not a fraud probability; no match does not mean safe. Checks are not saved to history.</p>
    <div className="analysis-forms">
      <section className="panel">
        <h2>Message analysis</h2>
        <form className="analysis-form" onSubmit={event => { event.preventDefault(); if (text.trim()) analysis.mutate(); }}>
          <label>Channel<select disabled={analysis.isPending} value={channel} onChange={event => { setChannel(event.target.value); analysis.reset(); }}><option value="other">Other</option><option value="whatsapp">WhatsApp</option><option value="gmail">Gmail</option><option value="messenger">Messenger</option><option value="instagram">Instagram</option></select></label>
          <label>Message<textarea required disabled={analysis.isPending} maxLength={20000} rows={6} value={text} onChange={event => { setText(event.target.value); analysis.reset(); }} placeholder="Paste a non-sensitive test message" /></label>
          <button className="button-primary" type="submit" disabled={!text.trim() || analysis.isPending}>{analysis.isPending ? "Analyzing…" : "Analyze message"}</button>
        </form>
        {analysis.error && <p role="alert" className="form-error">{analysis.error.message}</p>}
        {analysis.data && <div className="analysis-result" aria-live="polite">
          <div className="analysis-verdict"><ScoreRing score={analysis.data.risk_score} level={analysis.data.risk_level} size={90} metric="Text similarity" /><RiskBadge level={analysis.data.risk_level} /></div>
          <ul>{analysis.data.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
          {analysis.data.previous_report_matches.length > 0 && <><h3>Matched patterns</h3><ul>{analysis.data.previous_report_matches.map(match => <li key={match.report_id}>{match.report_type} · {Math.round(match.similarity_score * 100)}% similarity · {match.status === "synthetic_demo" ? "synthetic demo" : "stored report"}</li>)}</ul></>}
          <p>Engine: database pattern matching. No AI service used. Not saved to history.</p>
        </div>}
      </section>
      <section className="panel">
        <h2>URL structure analysis</h2>
        <p className="analysis-description">Parses URL structure locally on the backend. It does not visit the website or verify that it is safe.</p>
        <form className="analysis-form" onSubmit={event => { event.preventDefault(); if (url.trim()) urlAnalysis.mutate(); }}>
          <label>URL<input required disabled={urlAnalysis.isPending} maxLength={4096} value={url} onChange={event => { setUrl(event.target.value); urlAnalysis.reset(); }} placeholder="https://example.com/" /></label>
          <button className="button-primary" type="submit" disabled={!url.trim() || urlAnalysis.isPending}>{urlAnalysis.isPending ? "Analyzing…" : "Analyze URL"}</button>
        </form>
        {urlAnalysis.error && <p role="alert" className="form-error">{urlAnalysis.error.message}</p>}
        {urlAnalysis.data && <div className="analysis-result" aria-live="polite">
          <span className="eyebrow">Parsed hostname</span><h3>{urlAnalysis.data.hostname}</h3>
          <p>Domain: {urlAnalysis.data.registrable_domain}</p>
          <ul>{urlAnalysis.data.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
          <p>No reputation or AI safety verdict is provided.</p>
        </div>}
      </section>
    </div>
  </div>;
}
