ocm-install-core
================

Installs Red Hat Advanced Cluster Management Operator with the MultiClusterHub (MCH).


Requirements
------------

The hosting cluster must be able to connect to an Operator Catalog that contains Red Hat Advanced Cluster Management as well as the image registries to support it.

Disconnected installs are possible provided that images are mirrored internally and then overriding the ocm_install_catalog* variables.


Role Variables
--------------

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_hub_kubeconfig      | yes                |                                    | Path to kubeconfig for the hub           |
| ocm_install_catalog     | no                 | redhat-operators                   | Catalog that contains the RHACM Operator |
| ocm_install_catalog_ns  | no                 | openshift-marketplace              | Namespace of the catalog                 |
| ocm_version             | no                 | 2.3.3                              | Desired RHACM version                    |
| ocm_channel             | no                 | release-2.3                        | Channel of the desired RHACM version     |


Dependencies
------------

The *kubernetes.core* collection from galaxy provides the connectivity to kubernetes clusters.

    collections:
      - kubernetes.core

The python modules *kubernetes* and *jmespath* are required to connect and extract values from the cluster resources.

    $ pip install kubernetes
    $ pip install jmespath


Example Playbook
----------------

An example of how to run this role with a well formed inventory.

Contents of inventory:

    [hub_cluster]
    test-cluster-1 kubeconfig=/path/to/kubeconfig1

    [managed_clusters]
    test-cluster-2 kubeconfig=/path/to/kubeconfig2
    test-cluster-3 kubeconfig=/path/to/kubeconfig3
    test-cluster-4 kubeconfig=/path/to/kubeconfig4

    [all:vars]
    ansible_python_interpreter=/path/to/venv/bin/python


tests/test.yml:

    - hosts: hub_cluster
      connection: local
      roles:
        - role: ../../ocm-install-core
          vars:
            ocm_hub_kubeconfig: "{{ hostvars[inventory_hostname].kubeconfig }}"
            ocm_install_catalog: internal-operators-catalog
            ocm_install_catalog_ns: internal-operators
            ocm_version: 2.4.0
            ocm_channel: release-2.4

Run the playbook with the inventory specified.

    $ ansible-playbook -i inventory test.yml
