export const appConfig = {
  USE_MOCK: import.meta.env?.VITE_USE_MOCK === "true",
  API_BASE_URL: import.meta.env?.VITE_API_BASE_URL ?? "/api",
  DEFAULT_MINUTES_SAVED_PER_CHECK: 2,
} as const;
