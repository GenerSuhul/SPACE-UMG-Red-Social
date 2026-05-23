# Stage 1: Build the Angular application
FROM node:20-alpine AS build

WORKDIR /usr/src/app

COPY package*.json ./

RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

# Stage 2: Serve the Angular application via Nginx
FROM nginx:alpine

# Copy custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled Angular files from build stage
# Angular 17+ compiles into dist/frontend/browser
COPY --from=build /usr/src/app/dist/frontend/browser /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
