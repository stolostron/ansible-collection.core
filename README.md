# Open Cluster Management Ansible Collection

An Ansible Collection that allows you to interact with OCM/ACM to provision and manage your Hybrid Cloud presence from the command line.

## Plugins

Dynamic Inventory for RHACM (pending)

## Roles

[ocm-install-core](roles/ocm-install-core/README.md)

[ocm-install-observability](roles/ocm-install-observability/README.md)

ocm-uninstall (pending)

[ocm-attach](roles/ocm-attach/README.md)

ocm-detach (pending)

## Modules

[ocmplus.cm.import_eks](plugins/modules/import_eks.py)

## Tests

### Sanity Test

Running sanity test:

    $ ansible-test sanity

### Integration Test

[Integration test for `ocmplus.cm.import_eks`](tests/integration/targets/import_eks/README.md)

## Disclaimer

This Ansible Collection is still in development but aims to expose OCM/ACM's functionality through a useful and simple Ansible Collection.  Some features may not be prsent, may be fully implemented, and may be buggy.  

## Contributing

See our [Contributing Document](CONTRIBUTING.md) for more information.  