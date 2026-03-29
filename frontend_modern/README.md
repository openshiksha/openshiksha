# OpenShiksha Frontend (Modern)

Modern React 18 + TypeScript + Vite frontend for OpenShiksha educational platform.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Router** - Navigation
- **React Query** - API state management
- **Axios** - HTTP client
- **KaTeX** - Math rendering
- **Recharts** - Analytics visualization

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend server running on http://localhost:8000

### Installation

```bash
npm install
```

### Development

```bash
# Start dev server on http://localhost:5173
npm run dev
```

### Build

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Code Quality

```bash
# Lint
npm run lint

# Type check
npm run type-check
```

## Project Structure

```
src/
├── api/           # API client and service functions
├── features/      # Feature-based modules (assignments, analytics, etc.)
├── shared/        # Shared components, hooks, utils
├── types/         # TypeScript type definitions
├── assets/        # Static assets
├── App.tsx        # Root component
└── main.tsx       # Entry point
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Development Phases

This frontend is being built in phases aligned with the 30-week modernization plan:

- **Phase 0**: ✅ Foundation and setup
- **Phase 1**: API integration and authentication
- **Phase 2**: Student features
- **Phase 3**: Teacher features
- **Phase 4**: Admin and parent features
- **Phase 5**: Question editor
- **Phase 6**: Polish and deploy

See `../../.claude/plans/proud-knitting-sonnet.md` for the full plan.
