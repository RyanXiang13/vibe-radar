# Use newer Node.js image (Required for Vite 6+)
FROM node:22-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package.json .

# Install dependencies
RUN npm install

# Copy app files
COPY . .

# Expose port
EXPOSE 5173

# Start the app
CMD ["npm", "run", "dev", "--", "--host"]