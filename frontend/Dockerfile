# --- Этап 1: Сборка ---
FROM node:20-alpine AS build

# Устанавливаем git для Vite (убирает WARN про commit hash)
RUN apk add --no-cache git

WORKDIR /app

# Копируем только package.json для кэширования слоёв
COPY package.json package-lock.json ./

# Устанавливаем зависимости (с кэшем BuildKit)
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Копируем исходники (без тестов, node_modules — см. .dockerignore)
COPY . .

# Собираем проект (tsc + vite build)
RUN npm run build


# --- Этап 2: Раздача ---
FROM nginx:alpine

# Удаляем дефолтный конфиг nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг и собранный фронтенд
COPY nginx.conf /etc/nginx/conf.d/
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]