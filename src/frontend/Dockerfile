# ==========================================
# Multi-stage Dockerfile for Vue 3 Frontend
# ==========================================

# Stage 1: Build Vue Application
FROM node:22-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy frontend source code and build
COPY . ./
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:1.27-alpine AS runner

# Remove default nginx static assets
RUN rm -rf /usr/share/nginx/html/*

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom Nginx configuration with reverse proxy for /api
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
