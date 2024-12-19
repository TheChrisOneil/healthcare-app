FROM node:16

# Set working directory
WORKDIR /app

# Install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy app source code
COPY . .

# Build React app
RUN npm run build

# Serve the built app
RUN npm install -g serve
CMD ["serve", "-s", "build"]

# Expose the React app's port
EXPOSE 3000
