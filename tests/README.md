# Testing

## Prerequisites

- Please make sure the collection root directory is located in ansible collections search path. (e.g. ~/.ansible/collections/ansible_collections/stolostron/core)
- Make sure you have installed ansible.
- Make sure you have an ACM (2.5+) cluster ready for integration tests.
- At least one managedcluster (not a local-cluster) is required to be imported on this cluster.

## Sanity

Run the following command:

```bash
make test-sanity
```

## Unit

Run the following command:

```bash
make test-unit
```

## Integration

Integration tests requires a hub_kubeconfig for a ACM 2.5+ cluster, and because we will use this file in the tests, we will not run the ansible-test in docker mode.

Use the following steps to run integration tests:

1. [Optional] Install dependencies if not installed before:
   ```
    pip install -r tests/integration/requirements.txt
    ansible-galaxy install -r tests/integration/requirements.yml
   ```
2. Fill in the test variables:
   ```
    cp tests/integration/integration_config.yml.sample tests/integration/integration_config.yml
    vi tests/integration/integration_config.yml
   ```
3. Start tests:
   ```
   ansible-test integration
   ```
