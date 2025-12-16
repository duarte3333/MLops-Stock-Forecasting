#!/bin/bash
# Kubernetes Deployment Script for Stock Predictor API
# Usage: ./scripts/k8s-deploy.sh [create|deploy|delete|status|logs]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="mlops-cluster"
NAMESPACE="mlops-stock"
IMAGE_NAME="stock-predictor"
IMAGE_TAG="latest"

print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if kind is in PATH
check_kind() {
    if ! command -v kind &> /dev/null; then
        if [ -f "$HOME/.local/bin/kind" ]; then
            export PATH="$HOME/.local/bin:$PATH"
        else
            print_error "Kind not found. Please install it first."
            exit 1
        fi
    fi
}

# Create Kind cluster
create_cluster() {
    check_kind
    print_status "Creating Kind cluster: $CLUSTER_NAME"
    
    # Check if cluster already exists
    if kind get clusters 2>/dev/null | grep -q "^${CLUSTER_NAME}$"; then
        print_warning "Cluster '$CLUSTER_NAME' already exists"
        read -p "Do you want to delete and recreate it? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kind delete cluster --name $CLUSTER_NAME
        else
            return 0
        fi
    fi
    
    # Create cluster with config
    kind create cluster --config kind-config.yaml
    print_success "Cluster created successfully!"
    
    # Wait for cluster to be ready
    print_status "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=120s
    print_success "Cluster is ready!"
}

# Build and load Docker image
build_image() {
    print_status "Building Docker image: $IMAGE_NAME:$IMAGE_TAG"
    docker build -f Dockerfile.serve -t $IMAGE_NAME:$IMAGE_TAG .
    print_success "Image built successfully!"
    
    print_status "Loading image into Kind cluster..."
    kind load docker-image $IMAGE_NAME:$IMAGE_TAG --name $CLUSTER_NAME
    print_success "Image loaded into cluster!"
}

# Deploy to Kubernetes
deploy() {
    print_status "Deploying to Kubernetes..."
    
    # Apply all manifests
    kubectl apply -f k8s/namespace.yaml
    kubectl apply -f k8s/deployment.yaml
    kubectl apply -f k8s/service.yaml
    kubectl apply -f k8s/hpa.yaml
    
    print_success "Manifests applied!"
    
    # Wait for deployment
    print_status "Waiting for deployment to be ready..."
    kubectl rollout status deployment/stock-predictor-api -n $NAMESPACE --timeout=120s
    
    print_success "Deployment successful!"
    echo ""
    print_status "Service is available at: http://localhost:30080"
    echo ""
    kubectl get pods -n $NAMESPACE
}

# Install metrics-server (required for HPA)
install_metrics() {
    print_status "Installing metrics-server for HPA..."
    kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
    
    # Patch metrics-server for Kind (disable TLS verification)
    kubectl patch deployment metrics-server -n kube-system --type='json' -p='[
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-insecure-tls"},
      {"op": "add", "path": "/spec/template/spec/containers/0/args/-", "value": "--kubelet-preferred-address-types=InternalIP"}
    ]' 2>/dev/null || true
    
    print_success "Metrics-server installed!"
}

# Show status
status() {
    print_status "Cluster Status:"
    kubectl cluster-info 2>/dev/null || print_warning "Cluster not running"
    echo ""
    
    print_status "Pods in $NAMESPACE:"
    kubectl get pods -n $NAMESPACE -o wide 2>/dev/null || print_warning "Namespace not found"
    echo ""
    
    print_status "Services in $NAMESPACE:"
    kubectl get services -n $NAMESPACE 2>/dev/null || true
    echo ""
    
    print_status "HPA Status:"
    kubectl get hpa -n $NAMESPACE 2>/dev/null || true
    echo ""
    
    print_status "Recent Events:"
    kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' 2>/dev/null | tail -10 || true
}

# Show logs
logs() {
    POD_NAME=$(kubectl get pods -n $NAMESPACE -l app=stock-predictor -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
    if [ -n "$POD_NAME" ]; then
        print_status "Logs from $POD_NAME:"
        kubectl logs -n $NAMESPACE $POD_NAME --tail=100 -f
    else
        print_error "No pods found"
    fi
}

# Delete everything
delete() {
    print_status "Deleting Kubernetes resources..."
    kubectl delete -f k8s/ --ignore-not-found=true 2>/dev/null || true
    print_success "Resources deleted!"
}

# Delete cluster
delete_cluster() {
    check_kind
    print_status "Deleting Kind cluster: $CLUSTER_NAME"
    kind delete cluster --name $CLUSTER_NAME
    print_success "Cluster deleted!"
}

# Port forward (alternative to NodePort)
port_forward() {
    print_status "Port forwarding to localhost:8000..."
    kubectl port-forward -n $NAMESPACE svc/stock-predictor-service 8000:80
}

# Main
case "${1:-help}" in
    create)
        create_cluster
        ;;
    build)
        build_image
        ;;
    deploy)
        deploy
        ;;
    metrics)
        install_metrics
        ;;
    status)
        status
        ;;
    logs)
        logs
        ;;
    delete)
        delete
        ;;
    delete-cluster)
        delete_cluster
        ;;
    forward)
        port_forward
        ;;
    all)
        create_cluster
        build_image
        deploy
        install_metrics
        status
        ;;
    help|*)
        echo "Usage: $0 {create|build|deploy|metrics|status|logs|delete|delete-cluster|forward|all}"
        echo ""
        echo "Commands:"
        echo "  create         Create Kind cluster"
        echo "  build          Build and load Docker image"
        echo "  deploy         Deploy manifests to cluster"
        echo "  metrics        Install metrics-server (for HPA)"
        echo "  status         Show cluster and deployment status"
        echo "  logs           Stream logs from pods"
        echo "  delete         Delete K8s resources (keep cluster)"
        echo "  delete-cluster Delete the Kind cluster"
        echo "  forward        Port-forward service to localhost:8000"
        echo "  all            Run create + build + deploy + metrics"
        ;;
esac

