FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* /app/
RUN npm install

COPY . /app

ENV PORT=3000
EXPOSE 3000

RUN npm run build

CMD ["npm", "run", "start"]
