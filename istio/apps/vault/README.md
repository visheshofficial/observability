helm repo add hashicorp https://helm.releases.hashicorp.com
helm search repo hashicorp/vault


kubectl -n vault port-forward svc/vault 30000:8200

## Get the root token (dev mode):

If Deployment: kubectl -n vault logs deploy/vault | grep 'Root Token:' | head -n1
If StatefulSet: kubectl -n vault logs pod/vault-0 -c vault | grep 'Root Token:'

## UI login:
Open http://localhost:<forwarded-port> (the port you used in port-forward).
Auth method: Token
Paste the root token.

## CLI login (optional):
brew tap hashicorp/tap
brew install hashicorp/tap/vault
export VAULT_ADDR=http://127.0.0.1:<forwarded-port>
vault login <root-token>
