# Dotfiles

Personal dotfiles configuration, extending Omarchy.

## Overview

This setup provides:
- **kubectl** - Kubernetes cluster management
- **gcloud CLI** - GCP resource management and authentication

## Dependencies

### Google Cloud

Required packages:
- `google-cloud-cli`
- `google-cloud-cli-component-gke-gcloud-auth-plugin`
- `cloud-sql-proxy-bin`
- `google-cloud-cli-gsutil`

Install with:

```bash
yay -Syu google-cloud-cli google-cloud-cli-component-gke-gcloud-auth-plugin cloud-sql-proxy-bin google-cloud-cli-gsutil
```

### Kubernetes

Required packages:
- `kubectl`
- `kubectx`

Install with:

```bash
sudo pacman -Syu kubectl kubectx
```

## Setup

### Windsurf / VS Code Keyring

If VS Code or Windsurf fails to save the keyring with Gnome Keyring, add the following to the appropriate `argv.json` file:

```json
{
  "password-store": "gnome-libsecret"
}
```

**File locations:**
- Windsurf: `~/.windsurf/argv.json`
- VS Code: `~/.vscode/argv.json`

### Google Cloud

#### Initial Configuration

```bash
gcloud init
```

When prompted:
1. Add each project
2. Select `europe-west1-b` as the default region/zone (typically choice #18)

#### Rename Default Configuration

```bash
gcloud config configurations rename default --new-name=toolsense
```

#### Verify Configurations

```bash
gcloud config configurations list
```

Expected output:

```
NAME               IS_ACTIVE  ACCOUNT                      PROJECT            COMPUTE_DEFAULT_ZONE  COMPUTE_DEFAULT_REGION
toolsense          False      robert.nystrom@toolsense.io  toolsense          europe-west1-b        europe-west1
toolsense-dev      False      robert.nystrom@toolsense.io  toolsense-dev      europe-west1-b        europe-west1
toolsense-iot      True       robert.nystrom@toolsense.io  toolsense-iot      europe-west1-b        europe-west1
toolsense-iot-dev  False      robert.nystrom@toolsense.io  toolsense-iot-dev  europe-west1-b        europe-west1
```

### Kubernetes Clusters

#### Cluster Mapping

| Configuration      | Cluster Name                   | Location        |
|--------------------|--------------------------------|-----------------|
| toolsense          | toolsense-1                    | europe-west1-d  |
| toolsense-dev      | toolsense-1                    | europe-west1-d  |
| toolsense-iot      | gke-cluster-toolsense-iot-1    | europe-west1    |
| toolsense-iot-dev  | gke-cluster-toolsense-iot-1    | europe-west1    |

#### Add Cluster Credentials

Run the automated script:

```bash
./scripts/add-cluster-credentials.sh
```

<details>
<summary>Manual setup (if needed)</summary>

```bash
# toolsense
gcloud config configurations activate toolsense
gcloud container clusters get-credentials toolsense-1 --location=europe-west1-d

# toolsense-dev
gcloud config configurations activate toolsense-dev
gcloud container clusters get-credentials toolsense-1 --location=europe-west1-d

# toolsense-iot
gcloud config configurations activate toolsense-iot
gcloud container clusters get-credentials gke-cluster-toolsense-iot-1 --location=europe-west1

# toolsense-iot-dev
gcloud config configurations activate toolsense-iot-dev
gcloud container clusters get-credentials gke-cluster-toolsense-iot-1 --location=europe-west1
```

</details>

#### Configure kubectx Aliases

Run the automated script:

```bash
./scripts/setup-kubectx-aliases.sh
```

<details>
<summary>Manual setup (if needed)</summary>

```bash
kubectx toolsense=gke_toolsense_europe-west1-d_toolsense-1
kubectx toolsense-dev=gke_toolsense-dev_europe-west1-d_toolsense-1
kubectx toolsense-iot=gke_toolsense-iot_europe-west1_gke-cluster-toolsense-iot-1
kubectx toolsense-iot-dev=gke_toolsense-iot-dev_europe-west1_gke-cluster-toolsense-iot-1
```

</details>
