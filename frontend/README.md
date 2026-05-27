# SciLib Frontend

Modern React 18 + TypeScript frontend for the Scientific Library platform.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TanStack Query v5** - Data fetching & caching
- **Tailwind CSS** - Styling
- **shadcn/ui** - Component library
- **Zustand** - State management
- **React Router v6** - Routing
- **Playwright** - E2E testing
- **Vitest** - Unit testing

## Getting Started

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
# Install dependencies
npm install

# Copy environment file
cp .env.example .env
```

### Development

```bash
# Start dev server
npm run dev

# Open http://localhost:5173
```

### Building

```bash
# Production build
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Unit tests
npm run test

# Unit tests with coverage
npm run test:coverage

# E2E tests (requires running app)
npm run test:e2e

# All tests
npm run test:all
```

## Project Structure

```
src/
├── api/           # API client & interceptors
├── components/    # Reusable components
│   └── ui/        # shadcn/ui components
├── hooks/         # Custom React hooks
├── pages/         # Page components
├── store/         # Zustand stores
├── types/         # TypeScript types
├── lib/           # Utilities
└── mocks/         # MSW handlers for testing

tests/
├── unit/          # Unit tests
├── integration/   # Integration tests
└── e2e/           # E2E tests (Playwright)
```

## Features

- 🔐 Authentication with JWT refresh
- 📚 Library management (collections, items)
- 🔍 Search (simple, advanced, semantic)
- 👥 Groups & collaboration
- 📤 File upload with progress tracking
- 🌓 Light/dark theme support
- 📱 Responsive design

## API Configuration

Set `VITE_API_BASE_URL` in `.env`:

```env
VITE_API_BASE_URL=/api/v1
```

For local development against backend:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Docker

```bash
# Build image
docker build -t scilib-frontend .

# Run container
docker run -p 3000:80 scilib-frontend
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_BASE_URL` | Backend API URL | `/api/v1` |

## Code Style

- ESLint + Prettier configuration included
- TypeScript strict mode enabled
- Component naming: PascalCase
- File naming: camelCase.tsx

## Contributing

1. Create feature branch
2. Make changes
3. Write/update tests
4. Submit PR

## License

MIT
