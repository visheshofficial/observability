# Kind Cluster 
## Step 1: Create the Kind Cluster

Create the cluster using the provided configuration file:
```bash
kind create cluster --config istio/infrastructure/kind/kind-config.yaml --name istio-in-action-cluster
kubectl cluster-info --context kind-istio-in-action-cluster
kubectl get nodes
```
