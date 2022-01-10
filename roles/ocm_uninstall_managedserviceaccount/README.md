ocm_install_managedserviceaccount
=========

Removes the [Managed Service Account Addon](https://github.com/open-cluster-management-io/managed-serviceaccount) from a Red Hat Advanced Cluster Management Operator hub cluster.

Requirements
------------

The hosting cluster must already have Red Hat Advanced Cluster Management Operator installed and running:

```bash
$ oc get mch --all-namespaces
NAMESPACE                 NAME              STATUS    AGE
open-cluster-management   multiclusterhub   Running   19h
```

The controlling machine must have [Helm](https://github.com/helm/helm/releases) installed:

```bash
$ which helm
/usr/local/bin/helm
```

Role Variables
--------------

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_hub_kubeconfig      | yes                |                                    | Path to the kubeconfig file of the Red Hat Advanced Cluster Management hub cluster |

Dependencies
------------

The *kubernetes.core* collection from galaxy provides the capability to drive Helm.

```yaml
collections:
  - kubernetes.core
```

The controlling machine must have [Helm](https://github.com/helm/helm/releases) installed:

```bash
$ which helm
/usr/local/bin/helm
```

Example Playbook
----------------

An example of how to run this role with a well formed inventory

`tests/inventory`:

```yaml
[hub_cluster]
test-cluster-1 kubeconfig=/path/to/kubeconfig1

[all:vars]
ansible_python_interpreter=/path/to/venv/bin/python
```

`tests/test.yml`:

```yaml
- hosts: hub_cluster
  connection: local
  roles:
    - role: ../../ocm_install_managedserviceaccount
      vars:
        ocm_hub_kubeconfig: "{{ hostvars[inventory_hostname].kubeconfig }}"
```

Run the playbook with the inventory specified.

```bash
ansible-playbook -i inventory test.yml
```
