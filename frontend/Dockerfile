FROM oven/bun:1-alpine

WORKDIR /app

COPY package.json ./
RUN bun install

COPY . /app

ENV PORT=3000
EXPOSE 3000

RUN bun run build

CMD ["bun", "run", "start"]
