<!-- Taking from community.general and community.kubernetes -->
# Ansible Collection for Red Hat Advanced Cluster Management for Kubernetes Integration

This collection includes modules and plugins for driving Red Hat Advanced Cluster Management for Kubernetes functionality from Ansible Playbooks.

<!-- Nothing past the blurb is shown without opening full README -->

## Prerequisites

Before using this collection, install compatible versions of Red Hat Advanced Cluster Management for Kubernetes and Ansible (or Ansible Automation Platform). Review the following documentation for more information.

## Red Hat Advanced Cluster Management for Kubernetes version compatibility

Tested with Red Hat Advanced Cluster Management for Kubernetes version 2.5. All versions before 2.5 are not supported.

## Ansible version compatibility

Tested with stable versions of Ansible 2.10, Ansible 2.11, and Ansible 2.12. Ansible versions before 2.10 are not supported.

## Python support

Tested with Python 3.6, Python 3.7, Python 3.8, and Python 3.9. Python versions before 3.6 are not supported.

## Prepping your Red Hat Advanced Cluster Management for Kubernetes Hub cluster

Prior to using this collection, include the following configuration updates in the `MulticlusterHub` custom resource on your Hub cluster:

- Follow the instructions required for [Enabling cluster proxy add-ons](https://access.redhat.com/documentation/en-us/red_hat_advanced_cluster_management_for_kubernetes/2.5/html/clusters/managing-your-clusters#cluster-proxy-addon)
<!-- Above link isn't live yet. Code base link is here: https://github.com/stolostron/rhacm-docs/blob/2.5_stage/clusters/cluster_proxy_addon.adoc -->

- Run the following command to enable the Managed-ServiceAccount component (technical preview) in the `MultiClusterHub` custom resource. Replace `<multiclusterhub>` with the name of your MultiClusterHub component and `<namespace>` with the name of your project:
<!-- Official doc for this step doesn't exist yet (aimed for ACM 2.5). Once the doc for ACM exists, we need to remove this bullet and instead reference that doc -->
```bash
oc patch MultiClusterHub <multiclusterhub> -n <namespace> --type=json -p='[{"op": "add", "path": "/spec/overrides/components/-","value":{"name":"managedserviceaccount-preview","enabled":true}}]'
```

- Follow the instructions required for [Enabling ManagedServiceAccount add-ons (Technical Preview)](https://github.com/stolostron/rhacm-docs/blob/2.5_stage/multicluster_engine/addon_managed_service.adoc), starting with Step 2.
<!-- Official doc for this step doesn't exist yet (aimed for ACM 2.5). Once the doc for ACM exists, we need to reference that doc instead-->
## Included content

<!--start collection content-->
Name | Description
--- | ---
[stolostron.core.ocm_managedcluster](https://github.com/stolostron/ansible-collection.core/blob/main/docs/ocm_managedcluster_inventory.rst)| Fetch ocm managedclusters, and group clusters by labels. Hub cluster information will be stored in the "hub" group.
[stolostron.core.cluster_proxy](https://github.com/stolostron/ansible-collection.core/blob/main/docs/cluster_proxy_module.rst)| Install the cluster proxy on a managedcluster, and get proxy url from the addon. cluster-admin permission on hub is assumed to enable the plugin.
[stolostron.core.managedcluster_addon](https://github.com/stolostron/ansible-collection.core/blob/main/docs/managedcluster_addon_module.rst)| Use managedcluster_addon to enable/disable an addon on a managedcluster.
[stolostron.core.managed_serviceaccount](https://github.com/stolostron/ansible-collection.core/blob/main/docs/managed_serviceaccount_module.rst)| Use the managed-serviceaccount to setup a serviceaccount on a managedcluster, and return the serviceaccount token.
[stolostron.core.managed_serviceaccount_rbac](https://github.com/stolostron/ansible-collection.core/blob/main/docs/managed_serviceaccount_rbac_module.rst)| Use the managed-serviceaccount RBAC to setup a serviceaccount on a managedcluster with the specified RBAC permission.
[stolostron.core.cluster_management_addon](https://github.com/stolostron/ansible-collection.core/blob/main/docs/cluster_management_addon_module.rst)| Use cluster_management_addon to enable/disable a feature on the hub. Users can only install an addon on managed clusters if the feature of that addon is enabled. This plugin will need access to the Multicloudhub CR, and it enables/disables available features by updating the corresponding fields in the CR.
<!--end collection content-->

## Installation and Usage

### Installing the Collection from Ansible Galaxy

Before using the <COLLECTION_NAME> collection, you need to install it with the Ansible Galaxy CLI:

```bash
ansible-galaxy collection install <NAMESPACE_NAME>.<COLLECTION_NAME>
```

You can also include it in a `requirements.yml` file and install it via `ansible-galaxy collection install -r requirements.yml`, using the format:

```yaml
---
collections:
  - name: stolostron.core
    version: 0.0.1-alpha
```

### Using the `stolostron.core` Collection in your playbooks

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `stolostron.core.cluster_proxy_addon`:

```yaml
---
- hosts: "{{ target_hosts }}"
  connection: local

tasks:
- name: "Get ClusterProxy URL for {{ hostvars[inventory_hostname].cluster_name }}"
  stolostron.core.cluster_proxy_addon:
    hub_kubeconfig: "{{ hostvars['local-cluster'].kubeconfig }}"
    managed_cluster: "{{ hostvars[inventory_hostname].cluster_name }}"
    wait: True
    timeout: 60
  register: cluster_proxy_url
```

For documentation on how to use individual modules and other content included in this collection, please see the links in the 'Included content' section earlier in this README.

## Development

If you want to develop new content for this collection or improve what's already here, the easiest way to work on the collection is to clone it into one of the configured [`COLLECTIONS_PATHS`](https://docs.ansible.com/ansible/latest/reference_appendices/config.html#collections-paths), and work on it there.

## Testing

The `tests` directory contains configuration for running sanity, unit, and integration tests using [`ansible-test`](https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html).

For more information, see the [Testing README](https://github.com/stolostron/ansible-collection.core/blob/main/tests/README.md).

## Contributing to this collection

See [Contributing to `stolostron.core`](https://github.com/stolostron/ansible-collection.core/blob/main/CONTRIBUTING.md).

## Release Notes

See the [changelog](https://github.com/stolostron/ansible-collection.core/blob/changelogs/CHANGELOG.rst).

## More information

For more information, join the [`#forum-acm-devops-wg`](https://coreos.slack.com/archives/C014C2BF65D) channel on Slack.

## License

Licensed under the Apache License, Version 2.0.

See [LICENSE](https://github.com/stolostron/ansible-collection.core/blob/main/LICENSE) for full text.
