# --- Этап 1: Сборка ---
FROM node:20-alpine AS build
WORKDIR /app

# Копируем только package.json для кэширования
COPY package.json package-lock.json* ./
RUN npm install

# Копируем исходники и собираем
COPY . .
RUN npm run build

# --- Этап 2: Раздача ---
FROM nginx:alpine
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]