# Stage 1: build the application
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . ./

RUN npm run build

# Stage 2: Serve the application
FROM node:20-slim
WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/dist ./dist

EXPOSE 5173

CMD ["serve", "-s", "dist", "-l", "5173"]
