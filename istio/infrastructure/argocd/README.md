# ArgoCD Deployment and UI Access

## Deploy ArgoCD to Kind Cluster

```bash
helm repo add argo https://argoproj.github.io/argo-helm
helm repo update
kubectl create namespace argocd
helm install argocd argo/argo-cd \
  -n argocd \
  --create-namespace \
  -f argo-value/argocd-values.yaml
kubectl get pods -n argocd
kubectl get svc -n argocd
```

## Access ArgoCD UI

- Open your browser and go to:
  ```
  http://localhost:32080
  ```
  (This matches the NodePort and hostPort mapping in your Kind and ArgoCD configs.)

## Get ArgoCD Admin Password

Run the following command to retrieve the initial admin password:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 --decode
```
Use username `admin` and the password from above to log in.

---

If you change the NodePort or hostPort, update both your Kind and ArgoCD configuration files accordingly.

