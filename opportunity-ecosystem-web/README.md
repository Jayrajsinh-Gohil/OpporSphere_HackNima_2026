# OpporSphere — Web Frontend

> Next.js 16 frontend for the OpporSphere platform. See the [root README](../README.md) for the full project overview and setup guide.

## Getting Started

```bash
# Install dependencies
npm install

# Fill in your environment variables
cp .env.example .env.local
# → Edit .env.local with your Supabase keys

# Start the development server (Turbopack)
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Pages

| Route | Description |
|-------|-------------|
| `/` | Landing page with feature overview and API status |
| `/login` | Sign in with Google or email/password |
| `/signup` | Create a new student account |
| `/onboarding` | Set up your profile (skills, interests, goals) |
| `/dashboard` | Personalized opportunity feed + AI recommendations |
| `/discovery` | Smart NLP search for opportunities |
| `/opportunities` | Browse all opportunities with filters |
| `/team-finder` | Find teammates for hackathons and events |
| `/profile` | View and edit your student profile |

## Environment Variables

```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Scripts

```bash
npm run dev        # Start dev server (Turbopack)
npm run build      # Production build
npm run start      # Start production server
npm run lint       # Run ESLint
npm test           # Run unit tests (vitest)
npm run test:e2e   # Run E2E tests (Playwright)
```

## Tech Stack

- **Framework:** Next.js 16 with App Router
- **Language:** TypeScript
- **Styling:** Tailwind CSS v4
- **Auth:** Supabase JS SDK
- **UI Icons:** Lucide React
- **Testing:** Vitest + Testing Library + Playwright
