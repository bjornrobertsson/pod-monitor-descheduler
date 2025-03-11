# Build the image
docker build -t $REGISTRY/pod-monitor:latest .

# Push the image
docker push $REGISTRY/pod-monitor:latest
