# BAS App

Main web application. Built with Next.js 16, TypeScript, and Tailwind CSS v4.

## Stack

| Layer | Choice | Reason |
|---|---|---|
| Framework | Next.js 16 (App Router) | SSR + SSG + API routes; Vercel-native |
| Language | TypeScript | Type safety, maintainability |
| Styling | Tailwind CSS v4 | Utility-first; design-system ready |
| Linting | ESLint (Next.js config) | React/Next.js best practices |
| Formatting | Prettier + prettier-plugin-tailwindcss | Consistent style; sorted Tailwind classes |
| CI | GitHub Actions | Lint + typecheck + build on every push/PR |
| Deployment | Vercel | Zero-config Next.js hosting |

## Getting started

```bash
npm install
npm run dev       # http://localhost:3000
```

## Scripts

| Script | Description |
|---|---|
| `npm run dev` | Start dev server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run typecheck` | TypeScript compiler check |
| `npm run format` | Format all files with Prettier |
| `npm run format:check` | Check formatting (CI) |

## Project structure

```
src/
  app/           # App Router pages and layouts
    layout.tsx
    page.tsx
    globals.css
  components/    # Shared UI components
  lib/           # Utilities and helpers
```

## CI / Deployment

Push to `main` → GitHub Actions CI (lint → typecheck → build) → Vercel auto-deploy.

Vercel project settings: Framework = Next.js, Root directory = `/`.
