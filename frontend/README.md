# ResuMatch AI — Frontend

React 19 + TypeScript + Vite + Tailwind CSS v4

## Prerequisites

- Node.js 20+
- Backend running on `http://localhost:8000` (see root README)

## Setup

```bash
npm install
npm run dev
```

Opens at `http://localhost:5173`. API requests to `/api/*` are proxied to the backend automatically via `vite.config.ts`.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server with HMR |
| `npm run build` | Type-check and build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint |

## Project Structure

```
src/
├── components/
│   ├── chatbot/       # AI assistant chat UI
│   ├── layout/        # Dashboard shell
│   ├── match/         # Match cards, skill radar chart
│   └── ui/            # Shared UI (animated background, loaders)
├── context/           # CandidateContext — shared candidate state
├── pages/             # Route-level components
│   ├── Login.tsx
│   ├── ParseResume.tsx
│   ├── Candidates.tsx
│   └── JobMatch.tsx
├── utils/
│   └── api.ts         # Axios client (base URL + auth header)
├── App.tsx            # Router setup
└── index.css          # Tailwind v4 theme (CSS variables)
```

## Notes

- Tailwind v4 — theme is defined via CSS variables in `src/index.css`, not `tailwind.config.js` (that file is unused and can be deleted)
- Auth token is stored in `localStorage` and attached by `api.ts`
