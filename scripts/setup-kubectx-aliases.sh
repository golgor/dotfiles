#!/bin/bash
# Configure kubectx aliases for all clusters

set -e

echo "Setting up kubectx aliases..."

# Define kubectx aliases
declare -A ALIASES=(
    ["toolsense"]="gke_toolsense_europe-west1-d_toolsense-1"
    ["toolsense-dev"]="gke_toolsense-dev_europe-west1-d_toolsense-1"
    ["toolsense-iot"]="gke_toolsense-iot_europe-west1_gke-cluster-toolsense-iot-1"
    ["toolsense-iot-dev"]="gke_toolsense-iot-dev_europe-west1_gke-cluster-toolsense-iot-1"
)

# Create aliases
for alias in "${!ALIASES[@]}"; do
    context="${ALIASES[$alias]}"
    echo "  Creating alias: $alias -> $context"
    kubectx "$alias=$context"
done

echo ""
echo "✓ All kubectx aliases configured successfully!"
echo ""
echo "Available contexts:"
kubectx
