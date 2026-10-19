# --- Этап 1: Сборка ---
FROM node:20-alpine AS build

WORKDIR /app

# Копируем package.json и lock-файл (если есть) для кеширования слоев
COPY package.json package-lock.json* ./

# Устанавливаем зависимости
RUN npm install

# Копируем весь исходный код
COPY . .

# Собираем проект (создастся папка dist)
RUN npm run build

# --- Этап 2: Раздача ---
FROM nginx:alpine

# Удаляем дефолтный конфиг Nginx
RUN rm /etc/nginx/conf.d/default.conf

# Копируем наш конфиг
COPY nginx.conf /etc/nginx/conf.d/

# Копируем собранную статику из первого этапа
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]