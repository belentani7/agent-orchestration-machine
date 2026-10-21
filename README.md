# agent-orchestration-machine

> Professional project template

## 🚀 Quick Start

### Prerequisites
- Node.js >= 20.0.0
- pnpm >= 9.0.0

### Installation
```bash
# Clone the repository
git clone https://github.com/belentani7/agent-orchestration-machine.git
cd agent-orchestration-machine

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## 📦 Available Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server |
| `pnpm build` | Build for production |
| `pnpm preview` | Preview production build |
| `pnpm lint` | Run ESLint |
| `pnpm lint:fix` | Fix ESLint errors |
| `pnpm format` | Format with Prettier |
| `pnpm format:check` | Check formatting |
| `pnpm typecheck` | TypeScript type checking |
| `pnpm test` | Run unit tests |
| `pnpm test:watch` | Run tests in watch mode |
| `pnpm test:coverage` | Run tests with coverage |
| `pnpm test:e2e` | Run E2E tests |

## 🏗️ Architecture

```
src/
├── components/     # Reusable UI components
├── hooks/          # Custom React hooks
├── pages/          # Page components
├── services/       # Business logic & API calls
├── utils/          # Utility functions
├── styles/         # Global styles & theme
├── types/          # TypeScript types
├── test/           # Test utilities & setup
└── main.tsx        # Application entry point
```

## 🧪 Testing

- **Unit/Integration**: Vitest + React Testing Library
- **E2E**: Playwright
- **Coverage**: Target ≥ 80%

## 🔧 Code Quality

- **TypeScript**: Strict mode enabled
- **Linting**: ESLint + Biome
- **Formatting**: Prettier
- **Git Hooks**: Husky + lint-staged
- **Commits**: Conventional Commits enforced

## 🚢 Deployment

### Staging
Automatic on push to `main` branch.

### Production
Manual via GitHub Actions workflow dispatch or tag push.

## 📋 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔒 Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
