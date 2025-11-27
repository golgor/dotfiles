#!/bin/bash
# Add GKE cluster credentials for all configurations

set -e

echo "Adding cluster credentials for all configurations..."

# Define cluster configurations
declare -A CLUSTERS=(
    ["toolsense"]="toolsense-1:europe-west1-d"
    ["toolsense-dev"]="toolsense-1:europe-west1-d"
    ["toolsense-iot"]="gke-cluster-toolsense-iot-1:europe-west1"
    ["toolsense-iot-dev"]="gke-cluster-toolsense-iot-1:europe-west1"
)

# Iterate through each configuration
for config in "${!CLUSTERS[@]}"; do
    IFS=':' read -r cluster location <<< "${CLUSTERS[$config]}"
    
    echo ""
    echo "Processing: $config"
    echo "  Cluster: $cluster"
    echo "  Location: $location"
    
    gcloud config configurations activate "$config"
    gcloud container clusters get-credentials "$cluster" --location="$location"
done

echo ""
echo "✓ All cluster credentials added successfully!"
