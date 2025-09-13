# Prometheus Operator on kind + (Optional) Istio — Clean Step‑by‑Step Guide

This playbook condenses a long troubleshooting session into a crisp, reproducible flow. It targets a local **kind** cluster on macOS (Linux/Windows works similarly), installs **kube‑prometheus‑stack** (Prometheus Operator) safely, shows **alerting end‑to‑end**, and *optionally* integrates **Istio** metrics without breaking your monitoring stack.

> Assumptions
> - You have Homebrew (on macOS), Docker Desktop, and basic kubectl/helm skills.
> - Release name: `prometheus` and namespace: `monitoring`.
> - Prometheus selects ServiceMonitors/PodMonitors with label: `release: prometheus`.

---

## 0) Install CLI prerequisites

```bash
brew install kind kubectl helm
```

---

## 1) Create a kind cluster (simple default)

> If you need NodePorts exposed on the host, create a config; otherwise the default cluster works fine.

```bash
kind create cluster --name prometheus-cluster
kubectl cluster-info --context kind-prometheus-cluster
kubectl get nodes -o wide
```

---

## 2) Install kube‑prometheus‑stack (Prometheus Operator)

1) Create the namespace and add the Helm repo:

```bash
kubectl create namespace monitoring
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

2) Minimal, kind‑friendly values.yaml (save as `prometheus-values.yaml`):

```yaml
# prometheus-values.yaml
# Disable Grafana PVC on kind; use NodePort UIs for convenience

grafana:
  adminPassword: admin123
  service:
    type: NodePort
    nodePort: 30091
  persistence:
    enabled: false

prometheus:
  service:
    type: NodePort
    nodePort: 30090

alertmanager:
  service:
    type: NodePort
    nodePort: 30093

prometheusOperator:
  admissionWebhooks:
    enabled: true
    # Start with Ignore to avoid chicken‑and‑egg during first install; you can switch to Fail later
    failurePolicy: Ignore
    timeoutSeconds: 10
    deployment:
      enabled: true  # separate webhook pod for clarity
```

3) Install:

```bash
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --values prometheus-values.yaml \
  --wait
```

4) Verify pods:

```bash
kubectl get pods -n monitoring
```

You should see: operator, operator‑webhook, Prometheus STS, Alertmanager STS, Grafana, kube‑state‑metrics, node‑exporter.

> (Optional) After everything is Running, tighten the webhook policy:
>
> ```bash
> # Edit your file: set failurePolicy: Fail
> helm upgrade prometheus prometheus-community/kube-prometheus-stack \
>   --namespace monitoring \
>   --values prometheus-values.yaml \
>   --wait
> ```

Troubleshooting gotchas:
- If a webhook TLS secret mismatch blocks upgrades, delete the `prometheus-kube-prometheus-admission` secret and restart the webhook pod, or temporarily set `failurePolicy: Ignore`, upgrade, then switch back to `Fail`.
- On kind, PVC provisioners exist (local-path), but Grafana PVCs often complicate restarts—keeping persistence disabled is simplest.

---

## 3) Access the UIs (NodePorts)

```bash
echo "Prometheus:   http://localhost:30090"
echo "Grafana:      http://localhost:30091  (admin / admin123)"
echo "Alertmanager:  http://localhost:30093"
```

---

## 4) Understand the Prometheus ⇄ Alertmanager wiring

Prometheus auto‑discovers Alertmanager via Kubernetes service discovery; no hardcoded IPs. Check in Prometheus UI → **Status → Configuration** → `alerting:` to see the discovered `prometheus-kube-prometheus-alertmanager` service on port `http-web` (9093).

Quick validation:

```bash
# Alertmanager targets
curl -s http://localhost:30090/api/v1/alertmanagers | jq .
# Prometheus targets page (browser): http://localhost:30090/targets
```

---

## 5) Single, clean test alert — full lifecycle

Create `simple-alert.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: simple-test-alert
  namespace: monitoring
  labels:
    release: prometheus  # MUST match your Prometheus .spec.ruleSelector
spec:
  groups:
  - name: simple.rules
    rules:
    - alert: SimpleAlert
      # Match a real job name from Prometheus → Status → Targets; example below:
      expr: up{job="prometheus-kube-prometheus-prometheus"} == 1
      for: 30s
      labels:
        severity: warning
      annotations:
        summary: "Prometheus is up"
        description: "Fires when Prometheus target reports up==1 (demo)."
```

Apply and verify:

```bash
kubectl apply -f simple-alert.yaml
# Prometheus UI → Alerts: should go Active → Pending (30s) → Firing
# Alertmanager UI → see the alert instance(s) grouped by alertname
```

Common reasons an alert doesn’t appear:
- **Missing labels** on the `PrometheusRule` that Prometheus expects (e.g., `release: prometheus`).
- Wrong job label in the expression. Confirm job names in **Status → Targets**.

Cleanup the demo rule:

```bash
kubectl delete -f simple-alert.yaml
```

---

## 6) Admission webhook — what, why, and safe rollout

- The Prometheus Operator ships **admission webhooks** that validate/mutate `PrometheusRule` and `AlertmanagerConfig` objects, preventing bad rules from breaking Prometheus.
- Two deployment styles:
  - **Embedded** (inside operator pod): `deployment.enabled: false`
  - **Standalone** (separate pod): `deployment.enabled: true` (recommended for clarity)
- Safe rollout pattern:
  1) Install/upgrade with `failurePolicy: Ignore` (avoids bootstrap deadlocks)
  2) Verify the webhook pod + TLS secret `prometheus-kube-prometheus-admission`
  3) Switch to `failurePolicy: Fail`

Quick checks:

```bash
kubectl get validatingwebhookconfigurations | grep prometheus
kubectl get mutatingwebhookconfigurations | grep prometheus
kubectl get pods -n monitoring | grep webhook
kubectl logs -n monitoring deploy/prometheus-kube-prometheus-operator | grep -i webhook || true
```

---

## 7) (Optional) Add Istio — safe, minimal metrics integration

### 7.1 Install Istio

```bash
curl -L https://istio.io/downloadIstio | sh -
cd istio-*/bin && export PATH="$PWD:$PATH"

istioctl x precheck
istioctl install -y --set values.defaultRevision=default  # creates istio-system
kubectl get pods -n istio-system
```

**Protect monitoring first** (avoid sidecars in Prometheus/Grafana/AM):

```bash
kubectl label namespace monitoring istio-injection=disabled --overwrite
```

### 7.2 Deploy a tiny test app with auto‑injection

`test-app.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: test-app
  labels:
    istio-injection: enabled
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin
  namespace: test-app
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
  template:
    metadata:
      labels: { app: httpbin }
    spec:
      containers:
      - name: httpbin
        image: kennethreitz/httpbin
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: httpbin
  namespace: test-app
  labels:
    app: httpbin
spec:
  selector:
    app: httpbin
  ports:
  - name: http
    port: 8000
    targetPort: 80
  # Expose Envoy’s metrics port so Prometheus can scrape sidecar metrics
  - name: http-monitoring
    port: 15090
    targetPort: 15090
```

Apply & generate a bit of traffic:

```bash
kubectl apply -f test-app.yaml
kubectl -n test-app wait --for=condition=ready pod -l app=httpbin --timeout=120s
kubectl run -n test-app curl-client --image=curlimages/curl:latest --rm -it --restart=Never -- \
  sh -lc 'curl -s http://httpbin:8000/get >/dev/null'
```

### 7.3 Wire Istio metrics into your existing Prometheus

**Control plane (istiod) ServiceMonitor** — create `istio-controlplane-servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-control-plane
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: istiod
  namespaceSelector:
    matchNames: ["istio-system"]
  endpoints:
  - port: http-monitoring   # 15014
    path: /metrics
    interval: 30s
    scrapeTimeout: 10s
```

**Sidecar metrics ServiceMonitor (per‑service)** — create `istio-sidecars-servicemonitor.yaml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-mesh
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: httpbin            # adjust per service OR use a PodMonitor variant below
  namespaceSelector:
    matchNames: ["test-app"]  # or your app namespaces
  endpoints:
  - port: http-monitoring     # 15090
    path: /stats/prometheus
    interval: 30s
    scrapeTimeout: 10s
```

Apply:

```bash
kubectl apply -f istio-controlplane-servicemonitor.yaml
kubectl apply -f istio-sidecars-servicemonitor.yaml
```

Check Prometheus Targets → look for:
- `istiod` target UP on `:15014/metrics`
- `httpbin` sidecar target UP on `:15090/stats/prometheus`

> **Alternative (broader):** Use a **PodMonitor** that scrapes all injected pods by selecting label `istio.io/rev` and the `http-envoy-prom`/`http-monitoring` port. This avoids per‑service ServiceMonitors but can raise cardinality; tune with relabeling if needed.

### 7.4 Validate mesh metrics

Run a few curls, then query in Prometheus (Graph):
- `istio_requests_total`
- `istio_request_duration_milliseconds_bucket`

You should see labels like `source_workload`, `destination_service_name`, `response_code`, and `connection_security_policy="mutual_tls"`.

**Keep monitoring outside the mesh** on kind unless you have headroom and a reason to mesh it; stateful pods (Grafana/Prometheus/Alertmanager) can have init‑container quirks with sidecars. If you *do* inject them, prefer per‑pod opt‑in annotations and test carefully.

---

## 8) Cleanup

```bash
# Remove test app
kubectl delete namespace test-app

# Remove the stack
helm uninstall prometheus -n monitoring
kubectl delete namespace monitoring

# Delete cluster when done
kind delete cluster --name prometheus-cluster
```

---

## Appendix — Quick commands

- See what labels your Prometheus expects on ServiceMonitor/PodMonitor/Rule:

```bash
kubectl -n monitoring get prometheus -o jsonpath='\
{range .items[*]}{.metadata.name}{"\n"}SM selector: {.spec.serviceMonitorSelector.matchLabels}{"\n"}\
PM selector: {.spec.podMonitorSelector.matchLabels}{"\n"}{end}'
```

- List all ServiceMonitors/PodMonitors Prometheus can see:

```bash
kubectl get servicemonitors -A
kubectl get podmonitors -A
```

- Debug Alertmanager connectivity from Prometheus:

```bash
kubectl exec -n monitoring sts/prometheus-prometheus-kube-prometheus-prometheus -- \
  wget -qO- http://localhost:9090/api/v1/alertmanagers | jq .
```

- Force Prometheus to reload dynamic configuration (targets & rules picked up automatically, but restart helps when stuck):

```bash
kubectl delete pod -n monitoring -l app.kubernetes.io/name=prometheus
```

