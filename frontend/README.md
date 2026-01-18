# ClashArena Frontend

A modern Next.js frontend for the ClashArena gaming platform.

## Features

- **Modern UI/UX**: Built with Tailwind CSS and Headless UI
- **Authentication**: Complete login/register system with JWT
- **Responsive Design**: Mobile-first approach
- **TypeScript**: Full type safety
- **API Integration**: Seamless backend communication

## Tech Stack

- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS
- Headless UI
- Heroicons
- Axios
- React Query

## Getting Started

1. Install dependencies:
```bash
npm install
```

2. Create environment file:
```bash
# Create .env.local with:
NEXT_PUBLIC_API_URL=http://localhost:8001
```

3. Start development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

```
src/
├── app/                    # Next.js app directory
│   ├── dashboard/         # User dashboard
│   ├── login/            # Login page
│   ├── register/         # Registration page
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Home page
├── components/           # Reusable components
│   └── Navbar.tsx       # Main navigation
├── contexts/            # React contexts
│   └── AuthContext.tsx  # Authentication context
└── lib/                 # Utilities
    ├── api.ts          # API client
    ├── types.ts        # TypeScript types
    └── utils.ts        # Helper functions
```

## API Integration

The frontend communicates with the ClashArena backend API running on `http://localhost:8001`.

### Authentication Flow

1. User registers/logs in
2. JWT token is stored in localStorage
3. Token is automatically included in API requests
4. Protected routes redirect to login if not authenticated

### Key Endpoints

- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user
- `GET /wallet/balance` - Get wallet balance
- `GET /matches` - Get user matches

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Code Style

- Use TypeScript for all components
- Follow Next.js App Router patterns
- Use Tailwind CSS for styling
- Implement proper error handling
- Add loading states for better UX

## Deployment

The frontend can be deployed to:

- Vercel (recommended for Next.js)
- Netlify
- AWS Amplify
- Any static hosting service

Make sure to set the `NEXT_PUBLIC_API_URL` environment variable to your production API URL.