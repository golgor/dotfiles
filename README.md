# dotfiles
Dotfiles for my personal setup. It is an extension of Omarchy.

The full setup provides the following:
- kubectl - For managing clusters.
- gcloud cli - For managing GCP resources and authentication.

## Dependencies
### Google Cloud
The packages necessary for the gcloud command is:
- google-cloud-cli
- google-cloud-cli-component-gke-gcloud-auth-plugin
- cloud-sql-proxy-bin

These can be installed with the following command:

```bash
yay -Syu google-cloud-cli google-cloud-cli-component-gke-gcloud-auth-plugin cloud-sql-proxy-bin
```

### Kubernetes
The packages necessary for Kubernetes workflow is:
- kubectl
- kubectx

These can be installed with the following command:

```bash
sudo pacman -Syu kubectl kubectx
```

