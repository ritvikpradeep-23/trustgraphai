import { appConfig } from "../config/appConfig.ts";
import { demoUser, mockDetections } from "./mockData.ts";
import type { Detection, ExtensionStatus, Settings, User } from "@/types/trustgraph";

const DETECTIONS_KEY = "trustgraph_mock_detections_v1";
const USER_KEY = "trustgraph_mock_user_v1";
const SETTINGS_KEY = "trustgraph_mock_settings_v1";
const STATUS_KEY = "trustgraph_mock_status_v1";
const read = <T>(storage: Storage, key: string, fallback: T): T => {
  try { const value = storage.getItem(key); return value ? JSON.parse(value) as T : fallback; }
  catch { return fallback; }
};
const write = (storage: Storage, key: string, value: unknown) => {
  try { storage.setItem(key, JSON.stringify(value)); }
  catch { throw new Error("This browser could not save your changes. Check that browser storage is available."); }
};

export const getDetections = (): Detection[] => {
  const value = read(localStorage, DETECTIONS_KEY, mockDetections);
  return Array.isArray(value) && value.every(item => item && typeof item.id === "string" && Number.isFinite(Date.parse(item.createdAt)) && typeof item.site === "string" && typeof item.channel === "string" && typeof item.riskScore === "number" && Number.isFinite(item.riskScore) && ["SAFE", "LOW", "CAUTION", "HIGH", "CRITICAL"].includes(item.riskLevel) && Array.isArray(item.signals) && item.signals.every(signal => signal && typeof signal.name === "string" && typeof signal.explanation === "string" && typeof signal.score === "number")) ? value : mockDetections;
};
export const setDetections = (value: Detection[]) => write(localStorage, DETECTIONS_KEY, value);
export const resetDetections = () => setDetections(mockDetections);
export const getUser = (): User | null => {
  const user = read<User | null>(sessionStorage, USER_KEY, null) ?? read<User | null>(localStorage, USER_KEY, null);
  return user && typeof user.name === "string" && user.name.trim() && typeof user.email === "string" && Number.isFinite(Date.parse(user.joinedAt)) ? user : null;
};
export const setUser = (value: User, remember = !sessionStorage.getItem(USER_KEY)) => {
  write(remember ? localStorage : sessionStorage, USER_KEY, value);
  (remember ? sessionStorage : localStorage).removeItem(USER_KEY);
};
export const clearUser = () => { localStorage.removeItem(USER_KEY); sessionStorage.removeItem(USER_KEY); };
export const getSettings = (): Settings => {
  const currentUser = getUser();
  const user = currentUser ?? demoUser;
  const defaults: Settings = { name: user.name, email: user.email, minutesSavedPerCheck: appConfig.DEFAULT_MINUTES_SAVED_PER_CHECK, notifications: { security: true, detection: true, account: true }, extensionKey: "tg_demo_8f2c_4d1a" };
  const saved = read<Partial<Settings> | null>(localStorage, SETTINGS_KEY, null);
  const minutes = saved?.minutesSavedPerCheck;
  return { ...defaults, ...saved, name: currentUser?.name ?? (typeof saved?.name === "string" ? saved.name : defaults.name), email: currentUser?.email ?? (typeof saved?.email === "string" ? saved.email : defaults.email),
    minutesSavedPerCheck: typeof minutes === "number" && Number.isInteger(minutes) && minutes >= 1 && minutes <= 60 ? minutes : defaults.minutesSavedPerCheck,
    notifications: { security: typeof saved?.notifications?.security === "boolean" ? saved.notifications.security : true, detection: typeof saved?.notifications?.detection === "boolean" ? saved.notifications.detection : true, account: typeof saved?.notifications?.account === "boolean" ? saved.notifications.account : true },
    extensionKey: typeof saved?.extensionKey === "string" ? saved.extensionKey : defaults.extensionKey };
};
export const setSettings = (value: Settings) => write(localStorage, SETTINGS_KEY, value);
export const getStatus = (): ExtensionStatus => {
  const fallback: ExtensionStatus = { state: "CONNECTED", lastSeen: new Date().toISOString() };
  const value = read(localStorage, STATUS_KEY, fallback);
  return value && ["CONNECTED", "NOT CONNECTED", "UNKNOWN"].includes(value.state) ? { ...value, lastSeen: value.lastSeen && Number.isFinite(Date.parse(value.lastSeen)) ? value.lastSeen : null } : fallback;
};
export const setStatus = (value: ExtensionStatus) => write(localStorage, STATUS_KEY, value);
export const resetPreferences = () => localStorage.removeItem(SETTINGS_KEY);
export const clearWorkspace = () => {
  for (const key of [DETECTIONS_KEY, USER_KEY, SETTINGS_KEY, STATUS_KEY]) {
    localStorage.removeItem(key);
    sessionStorage.removeItem(key);
  }
  // Keep the deleted workspace empty instead of automatically restoring the demo seed.
  setDetections([]);
};
