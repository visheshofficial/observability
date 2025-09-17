# Chapter 02 — Accessing the Catalog service

This chapter shows different ways to reach the `catalog` service running in the namespace `istioinaction`.

Service/Workload recap:
- Service: `catalog` (ClusterIP), port 80 → targetPort 3000
- Deployment: `catalog`, containerPort 3000

## 1) In-cluster curl (ephemeral pod)

From a temporary curl pod, call the service via cluster DNS.

- From `default` namespace (works if mesh policy allows):
```
kubectl run -i -n default --rm --restart=Never dummy --image=curlimages/curl --command -- \
  sh -c 'curl -sS http://catalog.istioinaction/items/1'
```
Example output:
```
{
  "id": 1,
  "color": "amber",
  "department": "Eyewear",
  "name": "Elinor Glasses",
  "price": "282.00"
}
pod "dummy" deleted
```

- From `istioinaction` namespace (ensures sidecar/mTLS compatibility):
```
kubectl run -i -n istioinaction --rm --restart=Never dummy --image=curlimages/curl --command -- \
  sh -c 'curl -sS http://catalog.istioinaction/items/1'
```
Example output:
```
{
  "id": 1,
  "color": "amber",
  "department": "Eyewear",
  "name": "Elinor Glasses",
  "price": "282.00"
}
pod "dummy" deleted
```

Notes:
- If STRICT mTLS is enabled, calls from non-mesh pods (e.g., in `default` without injection) can fail. Using the same namespace as the service typically has injection enabled and works by default.

## 2) Port-forward the Service

Forward localhost to the Service’s port 80.
```
kubectl -n istioinaction port-forward svc/catalog 31080:80
```
Then in another terminal:
```
curl -sS http://localhost:31080/items/1
```

## 3) Port-forward the Deployment (direct to container)

Bypass the Service and forward directly to the pod’s containerPort 3000.
```
kubectl -n istioinaction port-forward deploy/catalog 31080:3000
curl -sS http://localhost:31080/items/1
```

## 4) Kind NodePort/hostPort (optional)

If your Kind cluster maps host ports to node ports, you can expose the app via a NodePort Service and match the mapped port.
- Change Service type to NodePort and set a fixed `nodePort` (e.g., 31080).
- Ensure Kind’s `extraPortMappings` forwards `hostPort: 31080` to the node.
- This approach may require recreating the Kind cluster to apply mapping changes.

## Troubleshooting

- Endpoints:
```
kubectl -n istioinaction get endpoints catalog -o wide
```
- Service selectors vs pod labels:
```
kubectl -n istioinaction describe svc catalog
kubectl -n istioinaction get pods -l app=catalog -o wide
```
- Logs:
```
kubectl -n istioinaction logs deploy/catalog -c catalog --tail=200
```
- Istio sidecar status (if using Istio):
```
istioctl proxy-status
```