# Cheetah Express Frontend 🐆

Modern React + TypeScript frontend for the Cheetah Express AI-powered delivery dispatch system.

## Features

- **Dashboard** - Real-time overview with KPIs and system status
- **Order Management** - Submit and track delivery orders with mock data
- **Driver Management** - Monitor driver fleet and performance
- **Call Sessions** - Real-time voice dispatch monitoring with AI sentiment analysis
- **Analytics** - Performance metrics and business intelligence
- **Order Details** - Complete audit trail visualization

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Lightning-fast build tool
- **TailwindCSS** - Utility-first CSS framework
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Recharts** - Beautiful charts and visualizations
- **Framer Motion** - Smooth animations
- **Lucide React** - Modern icon library
- **Axios** - HTTP client
- **Sonner** - Toast notifications

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Visit `http://localhost:3000`

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Layout.tsx
│   │   └── StatCard.tsx
│   ├── pages/           # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Orders.tsx
│   │   ├── OrderDetail.tsx
│   │   ├── Drivers.tsx
│   │   ├── CallSessions.tsx
│   │   └── Analytics.tsx
│   ├── utils/           # Utilities and API client
│   │   └── api.ts
│   ├── App.tsx          # Main app component
│   ├── main.tsx         # Entry point
│   └── index.css        # Global styles
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

## API Integration

The frontend connects to the backend API at `/api/v1`:

- `GET /mock/orders` - List available mock orders
- `POST /mock/orders/:id` - Submit a mock order
- `GET /orders/:id` - Get order status
- `GET /orders/:id/audit` - Get complete audit trail

## Design System

### Colors

- **Primary (Cheetah Orange)**: `#f97316`
- **Success**: `#10b981`
- **Error**: `#ef4444`
- **Warning**: `#f59e0b`
- **Info**: `#3b82f6`

### Components

- **StatCard** - Animated statistics cards
- **Layout** - Sidebar navigation with gradient
- **Motion Components** - Smooth page transitions

## Features Showcase

### Real-Time Call Sessions

Monitor voice dispatch calls with:
- Call outcome tracking (accepted/declined/no answer)
- AI sentiment analysis visualization
- Decline reason capture
- Call duration metrics

### Order Management

- Submit mock orders with one click
- Real-time processing status
- Complete audit trail visualization
- Compliance check results
- Driver ranking details

### Analytics Dashboard

- Order trend charts
- Vehicle type distribution
- Driver performance metrics
- Success rate tracking

## Development Tips

1. **Hot Reload**: Vite provides instant HMR
2. **Type Safety**: Full TypeScript support
3. **API Proxy**: Vite proxies `/api` to backend
4. **Mock Data**: Use mock orders for testing

## Deployment

### Netlify / Vercel

```bash
npm run build
# Deploy the dist/ folder
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "preview"]
```

## Contributing

1. Follow TypeScript best practices
2. Use Tailwind utility classes
3. Add proper type definitions
4. Test with mock data first

## License

MIT License - Part of Cheetah Express project

---

**Built with ❤️ using React + TypeScript + Vite**
