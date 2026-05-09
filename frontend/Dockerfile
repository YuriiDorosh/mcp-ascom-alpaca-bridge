# Build static assets; nginx serves them (browser calls API on host — set VITE_API_BASE accordingly).
FROM node:20-bookworm-slim AS build
WORKDIR /app
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
ARG VITE_API_BASE=http://127.0.0.1:8000
ENV VITE_API_BASE=${VITE_API_BASE}
RUN npm run build

FROM nginx:1.27-alpine
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
