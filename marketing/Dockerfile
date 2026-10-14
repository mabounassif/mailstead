FROM node:22-alpine AS build
WORKDIR /site
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run check && npm run build && npm run check:site

FROM node:22-alpine
WORKDIR /site
ENV NODE_ENV=production PORT=8000
COPY --from=build /site/dist ./dist
COPY --from=build /site/scripts/serve.mjs ./scripts/serve.mjs
USER node
EXPOSE 8000
CMD ["node", "scripts/serve.mjs"]
