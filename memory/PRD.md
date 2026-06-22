# Everstead PRD

## Original problem statement
Build a colorful, lively, production-quality marketing website and product front end for "Everstead", a tool that helps homeowners find the best clean energy setup (solar, wind, geothermal, micro-hydro, battery). A person enters their address and gets a plan with costs, savings, rebates, and a 3D view. Journey: Assess, Design, Purchase, Monitor, Optimize, Expand. Tagline "Let's energize your home." Primary button "Start my assessment". Plain friendly copy, no em dashes, no hype words, no generic AI-template look.

## User choices (this build)
1. Frontend only for assessment/marketplace data (served from a local MOCK file; the real engine is built separately in Claude Code).
2. Real email/password JWT auth with saved homes (retrofits) stored in MongoDB.
3. Realistic 3D home (React Three Fiber).
4. No third-party integrations now.
5. Warm/friendly font pairing chosen: Nunito (headings) + DM Sans (body).

## Architecture
- Frontend: React 19 (CRA + craco), React Router v7, Tailwind, framer-motion, Recharts, React Three Fiber + drei. One shared Layout (Navbar + Footer) wraps all pages; reusable CTA band.
- 3D home: `components/three/HouseDiorama.jsx` (low-poly house, solar array with shimmer, spinning turbine, battery, geothermal loop, trees, fence), wrapped by `HomeScene.jsx` (OrbitControls auto-rotate + drag, zoom/pan locked, ContactShadows) and `Home3D.jsx` (lazy + poster fallback).
- Data layer: `api/everstead.js` (assess/marketplace = local mock; auth + retrofits = real backend via REACT_APP_BACKEND_URL). `mock/mockData.js` matches API contract v1.
- Backend: FastAPI + MongoDB (motor). JWT Bearer auth (bcrypt). Endpoints under /api: auth/signup, auth/login, auth/me, auth/forgot-password, auth/oauth(501), retrofits CRUD (scoped to owner). Contract error envelope {error:{code,message,field}}.
- Auth: token in localStorage 'everstead_token'; AuthContext provides login/signup/me/logout.

## Pages implemented (2026-06-21)
- Home: 3D hero + animated stat chips, "What Everstead gives you" (6 cards), technology cards (5), 3-step preview, CTA band.
- How It Works: 5-step scroll journey with Recharts (monthly sunlight area, wind gauge, energy bars, interactive payback line + electricity-price slider, pay-vs-rebates donut), "What we measure" strip.
- About: styled placeholder (founder block "Photo coming soon", 3 mission cards).
- What's Next: 9 roadmap cards with Soon/Planned/Exploring tags.
- Retrofit My Home: multi-step wizard (start -> property -> energy -> checking -> results) with progress bar; results show 3D home, rebates box, 4 ranked tech cards, payback + 25-year charts; Save my results (routes to signup when logged out, then auto-saves) and Explore marketplace (placeholder toast).
- Login / Signup / Dashboard (saved homes + empty state + auto-save of pending plan) / Plan detail (reuses ResultsView).

## Status
- Backend: 19/19 pytest pass (auth + retrofits + cross-user isolation). Demo user demo@everstead.app / Everstead123!.
- Frontend: all flows verified by testing agent (iteration 2 = 100%). Duplicate auto-save bug fixed.
- Known minor (non-blocking): Recharts logs width(-1) warning on first mount; charts render fine. Benign WebGL context message on navigation.

## Backlog / next
- P1: Wire real backend assessment engine (POST /api/assess) when ready; remove frontend mock for assess.
- P1: Real Google/Apple OAuth (currently 501 stub + "coming soon").
- P2: Live marketplace page; performance monitoring dashboard; upload power bill.
- P2: Per-home 3D thumbnails rendered from the live scene; richer property 3D.
- P2: Silence Recharts measure warning (set min-height) and add explicit 3D context disposal.
