ocm-detach
==========

Detaches a managed cluster from an existing hub.

Requirements
------------

The controller must be able to communicate with both the hub and managed cluster.


Role Variables
--------------

The role will communicate with both the hub and managed cluster to unregister the managed cluster and uninstall the agents. It is idempotent, so if the agents are deleted, it will still execute successfully. The role can be safely run repeatedly for additional managed cluster entries in the inventory.


| Variable                      | Required           | Default                            | Comments                                 |
|-------------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_managedcluster_name       | yes                | validclustername                   | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`        |
| ocm_hub_kubeconfig            | yes                | /path/to/hub_kubeconfig            | Path to the hub's kubeconfig             |
| ocm_managedcluster_kubeconfig | no                 | /path/to/mc_kubeconfig             | Use for verification on managed cluster  |


Dependencies
------------

The *kubernetes.core* collection from galaxy provides the connectivity to kubernetes clusters.

    collection:
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

    [unmanaged_clusters]
    test-cluster-2 kubeconfig=/path/to/kubeconfig2

    [all:vars]
    ansible_python_interpreter=/path/to/venv/bin/python



Contents of test.yml:

    - hosts: unmanaged_clusters
      connection: local
      roles:
        - role: ../../ocm-detach
          vars:
            ocm_managedcluster_name: "{{ inventory_hostname }}"
            ocm_hub_kubeconfig: "{{ hostvars[groups['hub_cluster'][0]].kubeconfig }}"
            ocm_managedcluster_kubeconfig: "{{ hostvars[inventory_hostname].kubeconfig }}"

Run the playbook with the inventory specified.

    $ ansible-playbook -i inventory test.yml
