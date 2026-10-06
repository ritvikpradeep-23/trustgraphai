# TrustGraph frontend

The React/TypeScript workspace dashboard recovered from the Emergent preview, with corrected filters, analytics, settings, authentication-state handling, accessibility, and responsive layouts.

This app is separate from the existing plain-JavaScript browser extension in `../trustgraph_extension/`. It currently uses browser-local demo data. No production authentication, scoring backend, or live extension pairing is connected. Do not use a real password for the demo.

## Requirements

Use Node.js 22.18+ and npm. Dependencies are pinned in `package-lock.json`.

## Run

```bash
cd frontend
npm ci
npm run dev
```

Open the localhost URL printed by Vite. Sign in with any valid email address and a password of at least eight characters. Profile and detection preferences persist in this browser; remember-me controls whether the demo session persists across browser sessions.

## Verify and build

```bash
npm test
npm run build
npm run preview
```

Ten regression tests use isolated in-memory storage. They cover filtering, pagination, high/critical grouping, analytics totals, empty results, session persistence, profile/settings validation, account cleanup, and malformed storage. They do not delete browser data.

Vite writes the static production build to `dist/`. Configure the hosting provider to serve `index.html` for application routes such as `/app/analytics`. Generated output and `node_modules/` are intentionally not committed.

## Main routes

- `/`: public home, with informational pages at `/features`, `/how-it-works`, `/privacy`, `/about`, and `/contact`.
- `/login` and `/register`: demo authentication.
- `/app/dashboard`: overview and extension status.
- `/app/detections`: searchable, filterable result history and individual detail pages.
- `/app/analytics`: date-range analytics.
- `/app/profile` and `/app/settings`: account display and local preferences.

The preview's extension status/key are illustrative. Password changes and extension installation are explicitly unavailable. The contact form is a local demo and does not send inquiries. Export generates a JSON download; download completion could not be verified in the available in-app browser.

The service layer is in `src/services/` and demo behavior is in `src/mock/`. `src/config/appConfig.ts` currently enables mock mode. Integrating a production backend or connecting the extension is a separate task.
