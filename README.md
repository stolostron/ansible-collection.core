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

<!-- Looks like RST here -->
<!-- Instead of this, Ansible references Content tab (which does seem pretty clean) -->

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

<!-- We should include a changelog -->

## More information

For more information, join the [`#forum-acm-devops-wg`](https://coreos.slack.com/archives/C014C2BF65D) channel on Slack.

## License

Licensed under the Apache License, Version 2.0.

See [LICENSE](LICENSE) for full text.
