# --- Этап 1: Сборка ---
FROM node:20-alpine AS build

WORKDIR /app

# Копируем package.json и lock-файл для кеширования слоев
COPY package.json package-lock.json ./

# Устанавливаем зависимости
RUN npm ci

# Копируем только исходный код (тесты отсечены через .dockerignore)
COPY . .

# Собираем проект (tsc больше не видит тесты благодаря tsconfig)
RUN npm run build

# --- Этап 2: Раздача ---
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]