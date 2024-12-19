FROM nginx:latest

COPY min.conf /etc/nginx/nginx.conf
# # Copy the global configuration
# COPY nginx.conf /etc/nginx/nginx.conf

# # Copy the server configuration
# COPY default.conf /etc/nginx/conf.d/default.conf


# Expose port 80 for HTTP traffic
EXPOSE 80

# Start NGINX
CMD ["nginx", "-g", "daemon off;"]
