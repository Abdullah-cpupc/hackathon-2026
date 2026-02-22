# ChatBotAI Frontend

A modern Next.js frontend for ChatBotAI - AI chatbots for small businesses.

## Features

- **Next.js 15** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling
- **shadcn/ui** components
- **Authentication** with JWT tokens
- **Protected Routes** with middleware
- **Responsive Design** for all devices
- **Modern UI/UX** with animations

## Tech Stack

- **Framework**: Next.js 15
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **HTTP Client**: Axios
- **State Management**: React Context
- **Authentication**: JWT with cookies

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API running on `http://localhost:8000`

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment variables:**
   Create a `.env.local` file in the root directory:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```

4. **Open your browser:**
   Navigate to `http://localhost:3000`

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── auth/              # Authentication pages
│   │   │   ├── login/         # Login page
│   │   │   └── register/     # Registration page
│   │   ├── dashboard/         # User dashboard
│   │   ├── globals.css        # Global styles
│   │   ├── layout.tsx         # Root layout
│   │   └── page.tsx           # Landing page
│   ├── components/            # Reusable components
│   │   └── ui/               # shadcn/ui components
│   ├── contexts/             # React contexts
│   │   └── AuthContext.tsx   # Authentication context
│   ├── lib/                  # Utility functions
│   │   ├── api.ts           # API client
│   │   └── utils.ts         # Utility functions
│   └── middleware.ts         # Route protection middleware
├── components.json           # shadcn/ui configuration
├── tailwind.config.js        # Tailwind configuration
└── package.json             # Dependencies
```

## Authentication Flow

1. **Registration**: Users can create accounts with email, username, and password
2. **Login**: Users authenticate with username/password
3. **JWT Token**: Backend returns JWT token stored in HTTP-only cookies
4. **Protected Routes**: Middleware protects dashboard and other sensitive pages
5. **Auto-logout**: Token expiration automatically logs out users

## API Integration

The frontend communicates with the FastAPI backend through:

- **Auth API**: Login, register, get current user
- **Company API**: CRUD operations for companies
- **File API**: Upload and manage knowledge base files

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000/api/v1` |

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Connect repository to Vercel
3. Set environment variables
4. Deploy automatically

### Other Platforms

1. Build the project: `npm run build`
2. Deploy the `out` directory to your hosting platform
3. Set environment variables

## Features Overview

### Landing Page
- Modern hero section with gradient backgrounds
- Feature showcase with animated cards
- Pricing plans with clear CTAs
- Customer testimonials
- Responsive design for all devices

### Authentication
- Clean login/register forms
- Form validation and error handling
- Automatic redirects based on auth state
- Secure token management

### Dashboard
- User statistics and overview
- Company management interface
- File upload capabilities
- Responsive grid layouts

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.