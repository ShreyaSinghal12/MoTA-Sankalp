#!/bin/bash
set -e

echo "Building backend..."
docker build -f Dockerfile.backend -t mota-sankalp-backend:latest ./

echo "Building frontend..."
docker build -f Dockerfile.frontend -t mota-sankalp-frontend:latest ./

echo "Starting services with docker-compose..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 10

echo "Services are ready!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
