# Istio values (charts v1.27.1)

This folder contains Helm values files for installing and configuring Istio 1.27.1. These files are consumed by Argo CD Applications to deploy Istio components.

Charts source: https://istio-release.storage.googleapis.com/charts

## Files

- `base-values.yaml`
  - Values for the `istio/base` chart (CRDs and cluster-scoped resources). Typically minimal changes.
- `istiod-values.yaml`
  - Values for the `istio/istiod` control plane (meshConfig, pilot, images, resources).
- `ingressgateway-values.yaml`
  - Values for the ingress Gateway (Deployment/Service). Labeled `istio: ingressgateway`.
- `egressgateway-values.yaml`
  - Values for the egress Gateway (Deployment/Service). Labeled `istio: egressgateway`.

## Customize

Edit these YAMLs to change behavior. Common examples:

## Validate

- kubectl -n istio-system get deploy,svc
- kubectl -n istio-system get po -o wide
- kubectl -n istio-system logs deploy/istiod -c discovery --tail=200
