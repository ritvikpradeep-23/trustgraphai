import type { Detection, User } from "@/types/trustgraph";

const sites = [
  ["whatsapp", "WhatsApp Web"],
  ["gmail", "Gmail"],
  ["messenger", "Messenger"],
  ["instagram", "Instagram"],
  ["other", "LinkedIn"],
] as const;

const lowExplanations = [
  "Conversation patterns look consistent with an established contact and no unusual urgency was detected.",
  "The sender context is familiar and the observed language matches a routine conversation pattern.",
  "No strong indicators of impersonation or pressure were present in this result.",
];
const cautionExplanations = [
  "A new request introduces mild urgency and differs from the contact's recent conversation pattern.",
  "This result includes a combination of unusual timing and a domain that needs a closer look.",
  "The engine found a few signals worth verifying before taking action outside the conversation.",
];
const highExplanations = [
  "Multiple anomaly signals and an unusual request pattern were present in this result.",
  "The result shows a strong mismatch with prior contact behavior and a high-pressure action request.",
  "Several signals commonly associated with impersonation and account takeover were detected.",
];

const isoDay = (offset: number, hour: number) => {
  const date = new Date();
  date.setUTCDate(date.getUTCDate() - offset);
  date.setUTCHours(hour, (offset * 13) % 60, 0, 0);
  return new Date(Math.min(date.getTime(), Date.now())).toISOString();
};

export const mockDetections: Detection[] = Array.from({ length: 60 }, (_, index) => {
  const site = sites[index % sites.length];
  const riskLevel = index % 13 === 0 || index % 17 === 0 ? "HIGH" : index % 5 === 0 ? "CAUTION" : "LOW";
  const explanation = riskLevel === "HIGH" ? highExplanations[index % highExplanations.length] : riskLevel === "CAUTION" ? cautionExplanations[index % cautionExplanations.length] : lowExplanations[index % lowExplanations.length];
  const activeSignals = riskLevel === "HIGH" ? ["continuity", "similarity", "anomaly"] : riskLevel === "CAUTION" ? ["continuity", "anomaly"] : ["continuity", "similarity"];
  return {
    id: `TG-${String(2400 + index).padStart(5, "0")}`,
    createdAt: isoDay(index % 30, 8 + (index % 11)),
    channel: site[0],
    site: site[1],
    riskLevel,
    riskScore: riskLevel === "HIGH" ? 0.78 + (index % 6) / 100 : riskLevel === "CAUTION" ? 0.43 + (index % 8) / 100 : 0.04 + (index % 20) / 100,
    explanation,
    signals: [
      { name: "continuity", score: activeSignals.includes("continuity") ? 0.84 : 0, explanation: activeSignals.includes("continuity") ? "The conversation has continuity with known context." : "Continuity signal is not active yet." },
      { name: "similarity", score: activeSignals.includes("similarity") ? 0.72 : 0, explanation: activeSignals.includes("similarity") ? "The interaction resembles previously observed safe patterns." : "Similarity signal is not active yet." },
      { name: "precedent", score: 0, explanation: "Precedent is not active yet." },
      { name: "anomaly", score: activeSignals.includes("anomaly") ? 0.67 : 0, explanation: activeSignals.includes("anomaly") ? "Timing or behavior differs from the recent baseline." : "No meaningful anomaly is active yet." },
    ],
    confidence: index % 4 === 0 ? undefined : 0.81 + (index % 12) / 100,
    engineVersion: "v2.4.1",
    extracted: index % 3 === 0 ? { senderType: index % 2 ? "known contact" : "new contact", requestType: riskLevel === "HIGH" ? "account action" : "general conversation" } : undefined,
    urlIntelligence: index % 4 === 0 ? undefined : { domain: index % 2 ? "support-check.example" : "accounts-verify.example", reputation: riskLevel === "HIGH" ? "Needs review" : "No strong flags", age: index % 2 ? "3 months" : "4 years" },
    patternAnalysis: riskLevel === "HIGH" ? { match: "Impersonation pattern", detail: "Behavior overlaps with known account takeover patterns." } : undefined,
    recommendation: riskLevel === "HIGH" ? "Pause before responding and verify the sender through a number you already trust." : undefined,
    status: index % 4 === 0 ? "reviewed" : "new",
    feedback: "none",
    isDemo: true,
  };
});

export const demoUser: User = { id: "demo-user", name: "Alex Morgan", email: "alex@trustgraph.demo", joinedAt: "2025-11-04T09:00:00.000Z" };
