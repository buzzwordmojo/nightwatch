# Nightwatch Dashboard - Multi-arch Docker image
# Works on x86_64 (dev) and ARM64 (Raspberry Pi)

FROM node:20-slim AS builder

WORKDIR /app

# Build args for Next.js (needed at build time for NEXT_PUBLIC_* vars)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_CONVEX_URL=http://localhost:3210

ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_CONVEX_URL=$NEXT_PUBLIC_CONVEX_URL

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Production image
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production

# Copy built assets
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public/

EXPOSE 3000

CMD ["node", "server.js"]
