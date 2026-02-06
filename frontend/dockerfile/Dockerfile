# 1. Build Stage
FROM node:24-slim AS build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy source code and build
COPY . .
RUN npm run build

# 2. Production Stage (Using Nginx to serve static files)
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80 (standard for Nginx)
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]