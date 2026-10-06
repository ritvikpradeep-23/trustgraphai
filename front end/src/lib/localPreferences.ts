import type { Settings, User } from "../types/trustgraph.ts";
const key = "trustgraph_local_preferences_v1";
const defaults: Settings = { name: "Local workspace", email: "local-workspace@localhost.invalid", minutesSavedPerCheck: 2, notifications: { security: false, detection: false, account: false }, extensionKey: "Not configured" };
let memory = defaults;
export function getLocalPreferences(): Settings {
  try {
    const saved = JSON.parse(localStorage.getItem(key) ?? "null");
    return { ...defaults, name: typeof saved?.name === "string" && saved.name.trim() ? saved.name : defaults.name, minutesSavedPerCheck: Number.isInteger(saved?.minutesSavedPerCheck) && saved.minutesSavedPerCheck >= 1 && saved.minutesSavedPerCheck <= 60 ? saved.minutesSavedPerCheck : defaults.minutesSavedPerCheck };
  } catch { return { ...memory }; }
}
export function updateLocalPreferences(patch: Partial<Settings>) {
  if (patch.name !== undefined && !patch.name.trim()) throw new Error("Workspace name cannot be empty.");
  if (patch.minutesSavedPerCheck !== undefined && (!Number.isInteger(patch.minutesSavedPerCheck) || patch.minutesSavedPerCheck < 1 || patch.minutesSavedPerCheck > 60)) throw new Error("Enter a whole number from 1 to 60.");
  const current = getLocalPreferences();
  memory = { ...current, name: patch.name?.trim() ?? current.name, minutesSavedPerCheck: patch.minutesSavedPerCheck ?? current.minutesSavedPerCheck };
  try { localStorage.setItem(key, JSON.stringify(memory)); } catch { /* Session-only fallback if storage is unavailable. */ }
  return memory;
}
export function localWorkspaceIdentity(): User {
  const settings = getLocalPreferences();
  return { id: "local-workspace", name: settings.name, email: settings.email, joinedAt: new Date(2026, 9, 6).toISOString() };
}
