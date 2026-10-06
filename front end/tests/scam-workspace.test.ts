import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

test("dashboard has no extension connection indicator or status-loading gate", () => {
  const source = readFileSync(new URL("../src/pages/AppPages.tsx", import.meta.url), "utf8");
  const dashboard = source.slice(source.indexOf("export function DashboardPage"), source.indexOf("function FileClockIcon"));
  assert.ok(!dashboard.includes("extension-status"));
  assert.ok(!dashboard.includes("extensionService"));
  assert.ok(!dashboard.includes("status.isLoading") && !dashboard.includes("status.isError"));
  assert.ok(dashboard.includes("analyticsService") && dashboard.includes("detectionService"));
});

test("message analysis links to its saved result and describes ordered detection", () => {
  const source = readFileSync(new URL("../src/pages/AnalyzePage.tsx", import.meta.url), "utf8");
  assert.ok(source.includes("Saved to your account history"));
  assert.ok(source.includes("/app/detections/${analysis.data.detection_id}"));
  assert.ok(source.includes("Stored record matched; model skipped."));
  assert.ok(source.includes("No qualifying record match; original model used."));
});
