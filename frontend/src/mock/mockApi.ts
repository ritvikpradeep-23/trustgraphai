import { appConfig } from "../config/appConfig.ts";
import { getDetections, getSettings, getStatus, getUser, resetDetections, resetPreferences, setDetections, setSettings, setStatus, setUser, clearUser, clearWorkspace } from "./mockStore.ts";
import { demoUser } from "./mockData.ts";
import { buildAnalytics, filterDetectionList } from "../lib/detectionData.ts";
import type { DateRange, Detection, DetectionFilters, ExtensionStatus, Settings, User } from "@/types/trustgraph";

const wait = async <T>(value: T) => { await new Promise(resolve => setTimeout(resolve, 120)); return value; };

export const mockApi = {
  login: async (email: string, password: string, remember = true) => {
    email = email.trim().toLowerCase();
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email) || password.length < 8) throw new Error("Enter a valid email and a password of at least 8 characters.");
    const previous = getUser();
    const settings = getSettings();
    const name = previous?.email === email ? previous.name : settings.email === email ? settings.name : email === demoUser.email ? demoUser.name : email.split("@")[0].replace(/[._-]/g, " ").replace(/\b\w/g, letter => letter.toUpperCase());
    const user = { ...demoUser, email, name };
    setUser(user, remember);
    setSettings({ ...getSettings(), name, email });
    return wait(user);
  },
  register: async (name: string, email: string) => {
    name = name.trim(); email = email.trim().toLowerCase();
    if (!name || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) throw new Error("Enter your name and a valid email address.");
    const user = { ...demoUser, name, email, joinedAt: new Date().toISOString() };
    setUser(user);
    setSettings({ ...getSettings(), name, email });
    return wait(user);
  },
  logout: async () => { clearUser(); return wait(undefined); },
  deleteAccount: async () => { clearWorkspace(); return wait(undefined); },
  me: async () => wait(getUser()),
  detections: async (query: DetectionFilters) => wait(filterDetectionList(getDetections(), query)),
  detection: async (id: string) => wait(getDetections().find(item => item.id === id) ?? null),
  updateDetection: async (id: string, patch: Partial<Pick<Detection, "status" | "feedback">>) => {
    if (!getDetections().some(item => item.id === id)) throw new Error("This detection no longer exists.");
    const next = getDetections().map(item => item.id === id ? { ...item, ...patch } : item);
    setDetections(next);
    return wait(next.find(item => item.id === id) as Detection);
  },
  clearHistory: async () => { setDetections([]); return wait(undefined); },
  analytics: async (range?: DateRange) => wait(buildAnalytics(getDetections(), range)),
  status: async () => wait(getStatus()),
  setStatus: async (status: ExtensionStatus) => { setStatus(status); return wait(status); },
  settings: async () => wait(getSettings()),
  updateSettings: async (patch: Partial<Settings>) => {
    if (patch.name !== undefined && !patch.name.trim()) throw new Error("Profile name cannot be empty.");
    if (patch.minutesSavedPerCheck !== undefined && (!Number.isInteger(patch.minutesSavedPerCheck) || patch.minutesSavedPerCheck < 1 || patch.minutesSavedPerCheck > 60)) throw new Error("Enter a whole number from 1 to 60.");
    const next = { ...getSettings(), ...patch, name: patch.name?.trim() ?? getSettings().name, notifications: { ...getSettings().notifications, ...patch.notifications } };
    setSettings(next);
    const user = getUser();
    if (user && patch.name !== undefined) setUser({ ...user, name: next.name });
    return wait(next);
  },
  regenerateKey: async () => { const next = { ...getSettings(), extensionKey: `tg_demo_${crypto.randomUUID().replaceAll("-", "").slice(0, 16)}` }; setSettings(next); return wait(next); },
  reset: () => { resetDetections(); resetPreferences(); },
};

export const isMock = appConfig.USE_MOCK;
