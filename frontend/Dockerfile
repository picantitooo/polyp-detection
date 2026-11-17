FROM node:24-bookworm-slim AS build

WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN npm ci

COPY vite.config.ts tsconfig.json ./
COPY src ./src
COPY static ./static

ARG PUBLIC_API_URL=http://localhost:8000
ENV PUBLIC_API_URL=${PUBLIC_API_URL}
RUN npm run build

FROM node:24-bookworm-slim AS runtime

WORKDIR /app
ENV NODE_ENV=production \
    HOST=0.0.0.0 \
    PORT=3000
ARG PUBLIC_API_URL=http://localhost:8000
ENV PUBLIC_API_URL=${PUBLIC_API_URL}

COPY --from=build --chown=node:node /app/build ./build
COPY --from=build --chown=node:node /app/package.json ./package.json

USER node
EXPOSE 3000
CMD ["node", "build"]
