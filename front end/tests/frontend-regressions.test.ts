import { beforeEach, test } from "node:test";
import assert from "node:assert/strict";
import { buildAnalytics, dateRangeForDays, filterDetectionList } from "../src/lib/detectionData.ts";
import { mockApi } from "../src/mock/mockApi.ts";
import { getDetections, getSettings, getUser, setDetections } from "../src/mock/mockStore.ts";
import type { Detection } from "../src/types/trustgraph.ts";

class MemoryStorage {
  data = new Map<string, string>();
  getItem(key: string) { return this.data.get(key) ?? null; }
  setItem(key: string, value: string) { this.data.set(key, String(value)); }
  removeItem(key: string) { this.data.delete(key); }
  clear() { this.data.clear(); }
  get length() { return this.data.size; }
  key(index: number) { return [...this.data.keys()][index] ?? null; }
}
const local = new MemoryStorage(), session = new MemoryStorage();
Object.defineProperties(globalThis, { localStorage: { value: local, configurable: true }, sessionStorage: { value: session, configurable: true } });
beforeEach(() => { local.clear(); session.clear(); });

const now = new Date(2026, 9, 6, 12);
const detection = (id: string, daysAgo: number, riskLevel: Detection["riskLevel"] = "LOW"): Detection => {
  const time = new Date(now); time.setDate(time.getDate() - daysAgo);
  return { id, createdAt: time.toISOString(), channel: "gmail", site: "Gmail", riskLevel, riskScore: .5, explanation: "Test result", signals: [], engineVersion: "test", status: "new", feedback: "none", isDemo: true };
};
const items = [detection("older", 20), detection("today", 0, "HIGH"), detection("week", 6, "CAUTION"), detection("previous-week", 7, "CRITICAL")];

test("date filters include the whole selected first day and exclude older results", () => {
  const range = dateRangeForDays(7, now);
  assert.deepEqual(filterDetectionList(items, range).items.map(item => item.id), ["today", "week"]);
});
test("search is trimmed, risk filters work, and results sort newest first", () => {
  assert.equal(filterDetectionList(items, { q: " GMAIL ", level: "HIGH" }).total, 1);
  assert.deepEqual(filterDetectionList(items, { pageSize: 2 }).items.map(item => item.id), ["today", "week"]);
});
test("pagination clamps stale page numbers instead of producing an empty view", () => {
  const result = filterDetectionList(items, { page: 99, pageSize: 2 });
  assert.equal(result.page, 2); assert.equal(result.items.length, 2);
});
test("high-risk shortcut includes critical detections and malformed paging is safe", () => {
  assert.equal(filterDetectionList(items, { level: "HIGH_RISK" }).total, 2);
  const result = filterDetectionList(items, { page: NaN, pageSize: Infinity });
  assert.equal(result.page, 1); assert.equal(result.pageSize, 8); assert.equal(result.items.length, 4);
});
test("analytics ranges change totals and the final chart point matches the summary", () => {
  const week = buildAnalytics(items, dateRangeForDays(7, now), now);
  const month = buildAnalytics(items, dateRangeForDays(30, now), now);
  assert.equal(week.summary.total, 2); assert.equal(month.summary.total, 4);
  assert.equal(month.timeseries.at(-1)?.total, month.summary.total);
  assert.equal(month.summary.high, 2); assert.equal(month.summary.highRate, 50);
});
test("empty analytics stays zero and future records are excluded", () => {
  const result = buildAnalytics([detection("future", -1)], {}, now);
  assert.equal(result.summary.total, 0); assert.ok(result.timeseries.every(point => point.total === 0));
  assert.ok(result.distribution.every(item => item.count === 0));
});
test("remember me chooses persistent or session storage and logout clears both", async () => {
  await mockApi.login("  QA@EXAMPLE.COM  ", "demo-pass", false);
  assert.equal(getUser()?.email, "qa@example.com");
  assert.equal(local.getItem("trustgraph_mock_user_v1"), null);
  assert.ok(session.getItem("trustgraph_mock_user_v1"));
  await mockApi.logout(); assert.equal(getUser(), null);
  await mockApi.login("qa@example.com", "demo-pass", true);
  assert.ok(local.getItem("trustgraph_mock_user_v1")); assert.equal(session.getItem("trustgraph_mock_user_v1"), null);
});
test("profile edits update user identity and invalid settings do not overwrite saved values", async () => {
  await mockApi.login("qa@example.com", "demo-pass");
  await mockApi.updateSettings({ name: "  Jordan Lee  ", minutesSavedPerCheck: 5 });
  assert.equal(getUser()?.name, "Jordan Lee"); assert.equal(getSettings().name, "Jordan Lee");
  for (const value of [0, 61, NaN, 1.5]) await assert.rejects(mockApi.updateSettings({ minutesSavedPerCheck: value }));
  await assert.rejects(mockApi.updateSettings({ name: "   " }));
  assert.equal(getSettings().minutesSavedPerCheck, 5);
});
test("account deletion removes local workspace data and session", async () => {
  await mockApi.login("qa@example.com", "demo-pass");
  setDetections(items); await mockApi.updateSettings({ minutesSavedPerCheck: 5 });
  await mockApi.deleteAccount();
  assert.equal(getUser(), null); assert.deepEqual(getDetections(), []);
  assert.equal(local.getItem("trustgraph_mock_settings_v1"), null); assert.equal(session.length, 0);
});
test("malformed browser storage falls back safely", () => {
  local.setItem("trustgraph_mock_user_v1", JSON.stringify({ name: "Bad", email: "bad@example.com", joinedAt: "invalid" }));
  local.setItem("trustgraph_mock_detections_v1", JSON.stringify([{ id: "broken", riskScore: "invalid" }]));
  local.setItem("trustgraph_mock_settings_v1", JSON.stringify({ minutesSavedPerCheck: -4, notifications: { security: "yes" } }));
  assert.equal(getUser(), null); assert.equal(getDetections().length, 60);
  assert.equal(getSettings().minutesSavedPerCheck, 2); assert.equal(getSettings().notifications.security, true);
});
