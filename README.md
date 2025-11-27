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
- google-cloud-cli-gsutil

These can be installed with the following command:

```bash
yay -Syu google-cloud-cli google-cloud-cli-component-gke-gcloud-auth-plugin cloud-sql-proxy-bin google-cloud-cli-gsutil
```

### Kubernetes
The packages necessary for Kubernetes workflow is:
- kubectl
- kubectx

These can be installed with the following command:

```bash
sudo pacman -Syu kubectl kubectx
```

## Initialization
### Windsurf / VS Code Keyring
For some reason, sometimes VS Code, and thus Windsurf, fails to save the keyring. If Gnome Keyring is used, this can be fixed by specifying the `password-store` in the file `~/.windsurf/argv.json` by adding a key-value pair `"password-store": "gnome-libsecret"`.

For VS Code, this file is stored in `~/.vscode/argv.json`.

### Google Cloud
```bash
gcloud init
```

Each of the projects should be added and you should select `europe-west1-b` as 'Computation Region and Zone', which should be choice number 18. Listing the projects should look lite the following:
Change to europe-west1-d?

Renaming:
gcloud config configurations rename default --new-name=toolsense

```bash
> gcloud config configurations list
NAME               IS_ACTIVE  ACCOUNT                      PROJECT            COMPUTE_DEFAULT_ZONE  COMPUTE_DEFAULT_REGION
toolsense          False      robert.nystrom@toolsense.io  toolsense          europe-west1-b        europe-west1
toolsense-dev      False      robert.nystrom@toolsense.io  toolsense-dev      europe-west1-b        europe-west1
toolsense-iot      True       robert.nystrom@toolsense.io  toolsense-iot      europe-west1-b        europe-west1
toolsense-iot-dev  False      robert.nystrom@toolsense.io  toolsense-iot-dev  europe-west1-b        europe-west1
```

### Adding clusters

```bash
gcloud container clusters get-credentials CLUSTER_NAME --location=CONTROL_PLANE_LOCATION
```

- toolsense -> toolsense-1 europe-west1-d
- toolsense_dev -> toolsense-1 europe-west1-d
- toolsense_iot -> gke-cluster-toolsense-iot-1 europe-west1
- toolsense_iot_dev -> gke-cluster-toolsense-iot-1 europe-west1

You have to switch the Google Cloud Project accordingly.

gcloud config configurations activate toolsense
gcloud container clusters get-credentials toolsense-1 --location=europe-west1-d
gcloud config configurations activate toolsense-dev
gcloud container clusters get-credentials toolsense-1 --location=europe-west1-d
gcloud config configurations activate toolsense-iot
gcloud container clusters get-credentials gke-cluster-toolsense-iot-1 --location=europe-west1
gcloud config configurations activate toolsense-iot-dev
gcloud container clusters get-credentials gke-cluster-toolsense-iot-1 --location=europe-west1

kubectx toolsense=gke_toolsense_europe-west1-d_toolsense-1
kubectx toolsense-dev=gke_toolsense-dev_europe-west1-d_toolsense-1
kubectx toolsense-iot=gke_toolsense-iot_europe-west1_gke-cluster-toolsense-iot-1
kubectx toolsense-iot-dev=gke_toolsense-iot-dev_europe-west1_gke-cluster-toolsense-iot-1
