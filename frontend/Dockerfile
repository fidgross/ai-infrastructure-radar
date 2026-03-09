FROM node:20-alpine

WORKDIR /app/frontend

COPY package.json package-lock.json* ./

RUN npm install

COPY . /app/frontend

EXPOSE 3000
