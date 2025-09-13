# ArgoCD App-of-Apps Folder

Place child ArgoCD Application manifests here. Example template:

---
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sample-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/visheshofficial/observability
    targetRevision: HEAD
    path: path/to/your/app/manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: default
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
