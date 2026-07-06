# Stage 1: Build the React application
FROM node:20-alpine AS build

WORKDIR /app

# Copy package lock and configurations
COPY package*.json ./
RUN npm ci

# Copy codebase
COPY . ./

# Build production bundle
RUN npm run build

# Stage 2: Serve the built static files with Nginx
FROM nginx:alpine

# Copy built bundle from Stage 1 to Nginx HTML directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
