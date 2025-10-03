#!/bin/bash

# CSR Lambda Development Environment Setup Script
# バックエンドコンテナの起動と管理を自動化

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to check container health
check_container_health() {
    local container_name=$1
    local max_attempts=30
    local attempt=1
    
    print_status "Checking health of $container_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker ps --filter "name=$container_name" --filter "status=running" | grep -q $container_name; then
            print_success "$container_name is running"
            return 0
        fi
        
        print_status "Waiting for $container_name... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    print_error "$container_name failed to start properly"
    return 1
}

# Function to display service URLs
show_service_urls() {
    echo ""
    print_success "=== Development Environment Ready ==="
    echo -e "${GREEN}Backend API:${NC} http://localhost:8000"
    echo -e "${GREEN}Frontend:${NC} http://localhost:3000"
    echo -e "${GREEN}MySQL:${NC} localhost:3306"
    echo ""
    echo -e "${BLUE}API Documentation:${NC} http://localhost:8000/docs"
    echo -e "${BLUE}API Health Check:${NC} http://localhost:8000/"
    echo ""
}

# Function to show container status
show_status() {
    print_status "Container Status:"
    docker-compose ps
    echo ""
    
    # Check if services are responding
    if curl -s http://localhost:8000/ > /dev/null 2>&1; then
        print_success "Backend API is responding"
    else
        print_warning "Backend API is not responding"
    fi
    
    if curl -s http://localhost:3000/ > /dev/null 2>&1; then
        print_success "Frontend is responding"
    else
        print_warning "Frontend is not responding"
    fi
}

# Function to start development environment
start_dev() {
    print_status "Starting CSR Lambda development environment..."
    
    check_docker
    
    # Clean up any existing containers
    print_status "Cleaning up existing containers..."
    docker-compose down --remove-orphans
    
    # Start services
    print_status "Building and starting services..."
    docker-compose up --build -d
    
    # Wait for services to be healthy
    check_container_health "csr-lambda-mysql"
    check_container_health "csr-lambda-backend"
    check_container_health "csr-lambda-frontend"
    
    show_service_urls
}

# Function to stop development environment
stop_dev() {
    print_status "Stopping development environment..."
    docker-compose down
    print_success "Development environment stopped"
}

# Function to restart development environment
restart_dev() {
    print_status "Restarting development environment..."
    docker-compose restart
    
    check_container_health "csr-lambda-mysql"
    check_container_health "csr-lambda-backend"
    check_container_health "csr-lambda-frontend"
    
    show_service_urls
}

# Function to clean up everything
cleanup_dev() {
    print_status "Cleaning up development environment..."
    docker-compose down --volumes --remove-orphans
    docker system prune -f
    print_success "Cleanup completed"
}

# Function to show logs
show_logs() {
    local service=${1:-""}
    if [ -z "$service" ]; then
        print_status "Showing logs for all services..."
        docker-compose logs -f
    else
        print_status "Showing logs for $service..."
        docker-compose logs -f "$service"
    fi
}

# Function to show help
show_help() {
    echo "CSR Lambda Development Environment Manager"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the development environment"
    echo "  stop      Stop the development environment"
    echo "  restart   Restart the development environment"
    echo "  status    Show container status"
    echo "  logs      Show logs for all services"
    echo "  logs <service>  Show logs for specific service (backend, frontend, mysql)"
    echo "  cleanup   Clean up all containers and volumes"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 logs backend"
    echo "  $0 status"
}

# Main script logic
case "${1:-start}" in
    "start")
        start_dev
        ;;
    "stop")
        stop_dev
        ;;
    "restart")
        restart_dev
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs "$2"
        ;;
    "cleanup")
        cleanup_dev
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac