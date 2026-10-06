import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { analyzeService } from "@/services/analyzeService";
import { RiskBadge } from "@/components/common/RiskBadge";
import { ScoreRing } from "@/components/common/ScoreRing";

const patternSource = (status: string) => status === "synthetic_dataset" ? "ScamShield synthetic dataset" : status === "synthetic_demo" ? "synthetic demo" : "stored report";

export function AnalyzePage() {
  const queryClient = useQueryClient();
  const [text, setText] = useState("");
  const [channel, setChannel] = useState("other");
  const [url, setUrl] = useState("");
  const analysis = useMutation({ mutationFn: () => analyzeService.text(text.trim(), channel), onSuccess: () => {
    for (const key of ["analytics", "detections", "dashboard-detections"]) void queryClient.invalidateQueries({ queryKey: [key] });
  } });
  const urlAnalysis = useMutation({ mutationFn: () => analyzeService.url(url.trim()) });
  return <div className="page-stack">
    <div className="page-header"><div><span className="eyebrow">Your trust workspace</span><h1>Analyze a message or link.</h1><p>Keep the verdict in your account, not the message.</p></div></div>
    <p className="empty-period-note">The backend uses the original TrustGraph scam engine when its dependencies and weights are installed, plus the stored pattern catalog. Otherwise it explicitly falls back to pattern matching. Similarity and model review scores are not fraud probabilities; no match does not mean safe. Message text is processed transiently. Only verdict metadata is saved to your account; URL checks are not saved.</p>
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
          <div className="analysis-verdict"><ScoreRing score={analysis.data.risk_score} level={analysis.data.risk_level} size={90} metric={analysis.data.score_kind === "text-similarity" ? "Text similarity" : "Review score"} /><RiskBadge level={analysis.data.risk_level} /></div>
          <ul>{analysis.data.reasons.map((reason, index) => <li key={index}>{reason}</li>)}</ul>
          <h3>Signal hierarchy</h3>
          <p>Available engine signals, strongest first. Unavailable signals are not treated as zero. Each score is evidence, not fraud probability.</p>
          <ol>{Object.entries(analysis.data.signals).sort((a, b) => (b[1] ?? -1) - (a[1] ?? -1)).map(([name, score]) => <li key={name}>{name} · {score === null ? "unavailable" : `${(score * 100).toFixed(1)} / 100`}</li>)}</ol>
          {analysis.data.previous_report_matches.length > 0 && <><h3>Matched patterns</h3><ul>{analysis.data.previous_report_matches.map(match => <li key={match.report_id}>{match.report_type} · {Math.round(match.similarity_score * 100)}% similarity · {patternSource(match.status)}</li>)}</ul></>}
          <h3>Pattern hierarchy</h3>
          <p>{analysis.data.comparison_count} eligible patterns compared, ranked by actual similarity. Exact: 100%; very strong: 90–under 100%; strong: 80–under 90%; partial: {(analysis.data.match_threshold * 100).toFixed(1)}–under 80%. Below {(analysis.data.match_threshold * 100).toFixed(1)}% is not a detected match. These tiers describe resemblance, not certainty of fraud.</p>
          {analysis.data.comparison_count === 0 && <p>No comparable patterns. Messages need at least 24 normalized characters.</p>}
          {["Exact", "Very strong", "Strong", "Partial", "Below threshold"].map(tier => {
            const items = analysis.data!.pattern_comparisons.filter(match => match.tier === tier);
            if (!items.length) return null;
            return <details key={tier} open={tier !== "Below threshold"} className="pattern-tier"><summary>{tier} · {items.length} pattern{items.length === 1 ? "" : "s"}</summary><ol start={items[0].rank}>{items.map(match => <li key={match.report_id} value={match.rank}>{match.report_type} · {(match.similarity_score * 100).toFixed(1)}% similarity · {patternSource(match.status)}{match.rank === 1 ? " · closest pattern" : ""}</li>)}</ol></details>;
          })}
          <p>Engine: {analysis.data.method}. Original model {analysis.data.model_available ? "active" : "unavailable; catalog fallback active"}. Verdict metadata saved; message text not retained.</p>
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
