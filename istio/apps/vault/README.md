helm repo add hashicorp https://helm.releases.hashicorp.com
helm search repo hashicorp/vault


kubectl -n vault port-forward svc/vault 30000:8200

## Get the root token (dev mode):

If Deployment: kubectl -n vault logs deploy/vault | grep 'Root Token:' | head -n1
If StatefulSet: kubectl -n vault logs pod/vault-0 -c vault | grep 'Root Token:'

## UI login:
Open http://localhost:30000(the port you used in port-forward).
Auth method: Token
Paste the root token.

## CLI login (optional):
brew tap hashicorp/tap
brew install hashicorp/tap/vault
export VAULT_ADDR=http://127.0.0.1:30000
vault login root


## Enable Auth / Initial Setup

kubectl -n vault exec -it statefulset/vault -- sh

export VAULT_ADDR='http://127.0.0.1:8200'

vault auth enable kubernetes

vault policy write vault-secret-injection-policy - <<'EOF'
path "secret/data/vault-secret-injection/*" {
  capabilities = ["read"]
}
EOF


vault write auth/kubernetes/config \
  token_reviewer_jwt=@/var/run/secrets/kubernetes.io/serviceaccount/token \
  kubernetes_host="https://${KUBERNETES_PORT_443_TCP_ADDR}:443" \
  kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt

vault write auth/kubernetes/role/vault-secret-injection-role \
   bound_service_account_names=vault-secret-injection-sa \
   bound_service_account_namespaces=vaultinaction \
   policies=vault-secret-injection-policy \
   ttl=24h

//   audience="vault" removed for demo

vault kv put secret/vault-secret-injection/app-creds Username=Demo-user Password=Demo-pass