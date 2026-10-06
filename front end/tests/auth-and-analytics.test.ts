import { test } from "node:test";
import assert from "node:assert/strict";
import { validateLogin } from "../src/lib/authValidation.ts";
import { buildAnalytics } from "../src/lib/detectionData.ts";
import type { Detection } from "../src/types/trustgraph.ts";

test("login validation requires a real email and password without storing either", () => {
  assert.equal(validateLogin("", "").email, "Enter your email address.");
  assert.ok(validateLogin("missing-domain", "password").email);
  assert.ok(validateLogin("a@b.invalid", "").password);
  assert.ok(validateLogin("a@b.invalid", "a".repeat(129)).password);
  assert.deepEqual(validateLogin(" USER@example.invalid ", "valid passphrase"), {});
});
test("unknown results are represented and excluded from the assessed denominator", () => {
  const now = new Date("2026-10-06T12:00:00Z");
  const unknown: Detection = { id: "x", createdAt: now.toISOString(), channel: "other", site: "test",
    riskLevel: "UNKNOWN", riskScore: null, signals: [], explanation: "No match", engineVersion: "test",
    status: "new", feedback: "none", isDemo: false };
  const result = buildAnalytics([unknown], {}, now);
  assert.equal(result.summary.total, 1);
  assert.equal(result.summary.pending, 1);
  assert.equal(result.summary.low, 0);
  assert.equal(result.summary.highRate, null);
  assert.equal(result.distribution.reduce((sum, row) => sum + row.count, 0), 1);
});
test("invalid or reversed analytic ranges cannot generate malformed chart points", () => {
  for (const range of [{ from: "invalid" }, { from: "2027-01-01", to: "2026-01-01" }]) {
    assert.deepEqual(buildAnalytics([], range).timeseries, []);
  }
});

test("extension channels retain separate analytics counts", () => {
  const now = new Date("2026-10-06T12:00:00Z");
  const items = ["telegram", "discord", "slack", "linkedin"] as const;
  const data = items.map((channel, index): Detection => ({ id: String(index), createdAt: now.toISOString(),
    channel, site: channel, riskLevel: "CAUTION", riskScore: .8, signals: [], explanation: "Metadata",
    engineVersion: "browser-extension", status: "new", feedback: "none", isDemo: false }));
  const analytics = buildAnalytics(data, {}, now);
  for (const channel of items) assert.equal(analytics.channels.find(row => row.channel === channel)?.count, 1);
  assert.equal(analytics.channels.find(row => row.channel === "other")?.count, 0);
});
