<!-- Taking from community.general and community.kubernetes -->
# <COLLECTION_NAME>

This collection includes modules and plugins for driving Red Hat Advanced Cluster Management for Kubernetes functionality from Ansible Playbooks.

<!-- Nothing past the blurb is shown without opening full README -->

## Red Hat Advanced Cluster Management for Kubernetes version compatibility

Tested with Red hat Advanced Cluster Management for Kubernetes version 2.5. All versions before 2.5 are not supported.

## Ansible version compatibility

Tested with stable versions of Ansible 2.10, Ansible 2.11, and Ansible 2.12. Ansible versions before 2.10 are not supported.

## Python support

Tested with Python 3.6, Python 3.7, Python 3.8, and Python 3.9. Python versions before 3.6 are not supported.

## Included content

<!--start collection content-->
Name | Description
--- | ---
[ocmplus.cm.ocm_managedcluster](https://github.com/stolostron/ocmplus.cm/blob/main/docs/ocm_managedcluster_inventory.rst)| Fetch ocm managedclusters, and group clusters by labels. Hub cluster information will be stored in the "hub" group.
[ocmplus.cm.cluster_proxy](https://github.com/stolostron/ocmplus.cm/blob/main/docs/cluster_proxy_module.rst)| Install the cluster proxy on a managedcluster, and get proxy url from the addon. cluster-admin permission on hub is assumed to enable the plugin.
[ocmplus.cm.managedcluster_addon](https://github.com/stolostron/ocmplus.cm/blob/main/docs/managedcluster_addon_module.rst)| Use managedcluster_addon to enable/disable an addon on a managedcluster.
[ocmplus.cm.managed_serviceaccount](https://github.com/stolostron/ocmplus.cm/blob/main/docs/managed_serviceaccount_module.rst)| Use the managed-serviceaccount to setup a serviceaccount on a managedcluster, and return the serviceaccount token.
[ocmplus.cm.managed_serviceaccount_rbac](https://github.com/stolostron/ocmplus.cm/blob/main/docs/managed_serviceaccount_rbac_module.rst)| Use the managed-serviceaccount RBAC to setup a serviceaccount on a managedcluster with the specified RBAC permission.
[ocmplus.cm.cluster_management_addon](https://github.com/stolostron/ocmplus.cm/blob/main/docs/cluster_management_addon_module.rst)| Use cluster_management_addon to enable/disable a feature on the hub. Users can only install an addon on managed clusters if the feature of that addon is enabled. This plugin will need access to the Multicloudhub CR, and it enables/disables available features by updating the corresponding fields in the CR.
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
  - name: <NAMESPACE_NAME>.<COLLECTION_NAME>
    version: <COLLECTION_VERSION>
```

### Using the <COLLECTION_NAME> Collection in your playbooks

It's preferable to use content in this collection using their Fully Qualified Collection Namespace (FQCN), for example `<NAMESPACE_NAME>.<COLLECTION_NAME>.cluster_proxy_addon`:

```yaml
---
- hosts: "{{ target_hosts }}"
  connection: local

tasks:
- name: "Get ClusterProxy URL for {{ hostvars[inventory_hostname].cluster_name }}"
  <NAMESPACE_NAME>.<COLLECTION_NAME>.cluster_proxy_addon:
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

For more information, see the [Testing README](tests/README.md).

## Contributing to this collection

See [Contributing to <NAMESPACE_NAME>.<COLLECTION_NAME>](CONTRIBUTING.md).

## Release Notes

See the [changelog](https://github.com/stolostron/ocmplus.cm/blob/changelogs/CHANGELOG.rst).

## More information

For more information, join the [`#forum-acm-devops-wg`](https://coreos.slack.com/archives/C014C2BF65D) channel on Slack.

## License

Licensed under the Apache License, Version 2.0.

See [LICENSE](LICENSE) for full text.