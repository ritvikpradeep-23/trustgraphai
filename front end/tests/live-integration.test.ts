import { beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import { buildAnalytics, filterDetectionList } from "../src/lib/detectionData.ts";
import { getLocalPreferences, localWorkspaceIdentity, updateLocalPreferences } from "../src/lib/localPreferences.ts";
import type { Detection } from "../src/types/trustgraph.ts";

const storage = new Map<string, string>();
Object.defineProperty(globalThis, "localStorage", { configurable: true, value: {
  getItem: (key: string) => storage.get(key) ?? null,
  setItem: (key: string, value: string) => storage.set(key, value),
} });
beforeEach(() => storage.clear());
const now = new Date("2026-10-06T12:00:00Z");
const pending: Detection = { id: "pending", createdAt: now.toISOString(), channel: "other", site: "Backend", riskLevel: "PENDING", riskScore: null, signals: [{ name: "anomaly", score: null, explanation: "Unavailable" }], explanation: "AI unavailable", engineVersion: "test", status: "new", feedback: "none", isDemo: false, editable: false };

test("pending history never counts as low risk or a zero-percent assessed rate", () => {
  const result = buildAnalytics([pending], {}, now);
  assert.equal(result.summary.pending, 1);
  assert.equal(result.summary.low, 0);
  assert.equal(result.summary.highRate, null);
  assert.equal(result.distribution.find(item => item.label === "Pending")?.count, 1);
  assert.equal(filterDetectionList([pending], { level: "PENDING" }).total, 1);
});
test("risk rate excludes pending records from the assessed denominator", () => {
  const high = { ...pending, id: "high", riskLevel: "HIGH" as const, riskScore: .8 };
  assert.equal(buildAnalytics([pending, high], {}, now).summary.highRate, 100);
});
test("local preferences cannot enable authentication, notifications, or pairing", () => {
  const preferences = updateLocalPreferences({ name: "  Integration QA  ", minutesSavedPerCheck: 3, email: "not-used@example.com", extensionKey: "not-issued", notifications: { security: true, account: true, detection: true } });
  assert.equal(preferences.name, "Integration QA");
  assert.equal(localWorkspaceIdentity().id, "local-workspace");
  assert.equal(preferences.extensionKey, "Not configured");
  assert.equal(preferences.notifications.security, false);
  assert.equal(preferences.email, "local-workspace@localhost.invalid");
});
test("invalid preferences are rejected and malformed storage falls back safely", () => {
  for (const value of [0, 61, 1.5, NaN]) assert.throws(() => updateLocalPreferences({ minutesSavedPerCheck: value }));
  assert.throws(() => updateLocalPreferences({ name: "   " }));
  storage.set("trustgraph_local_preferences_v1", JSON.stringify({ name: "", minutesSavedPerCheck: -1 }));
  assert.equal(getLocalPreferences().minutesSavedPerCheck, 2);
});
