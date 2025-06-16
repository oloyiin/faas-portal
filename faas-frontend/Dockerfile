# Étape de build
FROM node:18-alpine as builder
WORKDIR /app

# Copier package.json et package-lock.json pour cache Docker
COPY package*.json ./

# Installer les dépendances
RUN npm ci

# Copier le reste du code
COPY . .

# Passer la variable d'environnement avant le build
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Construire l'application React
RUN npm run build

# Étape de production
FROM nginx:alpine

# Copier le build React dans le dossier servi par nginx
COPY --from=builder /app/build /usr/share/nginx/html

# Copier la configuration nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80

# Démarrer nginx en mode foreground
CMD ["nginx", "-g", "daemon off;"]