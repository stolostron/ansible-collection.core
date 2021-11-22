ocm-labels
==========

Manages labels on clusters managed by Red Hat Advanced Cluster Management (RHACM).


Requirements
------------

Clusters defined in the inventory should exist with valid authentication credentials.


Role Variables
--------------

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_hub_kubeconfig      | yes                |                                    | Path to kubeconfig for the hub           |
| ocm_managedcluster_name | yes                |                                    | Cluster for label change                 |
| ocm_merge_type          | no                 | preserve                           | (More Details Below)                     |
| ocm_user_labels         | yes                |                                    | Dictonary of desired labels              |
| ocm_protect_keys        | no                 | yes                                | Protect certain keys from change         |
| ocm_protected_keys      | no                 | (see defaults/main.yml)            | List of protected keys                   |

Example, User Labels:

    user:
      a: 10
      b: 20
      d: 40

Example, Cluster Labels:

    cluster:
      a: 1
      b: 2
      c: 3

| Merge Type                | Description                                                                                           | Result of Merge            |
|---------------------------|-------------------------------------------------------------------------------------------------------|----------------------------|
| preserve                  | If key already exists in cluster labels, do not overwrite.<br/>If keys does not exist, add the label. | {a: 1, b: 2, c: 3, d: 40}  |
| update                    | If key already exists in cluster labels, overwrite it.<br/>If key does not exist, add the label.      | {a: 10, b: 20, c:3, d: 40} |
| replace                   | Clear all cluster labels, then add user labels.                                                       | {a: 10, b: 20, d:40}       |
| delete                    | If key exists in cluster labels, delete it.<br/>If key does not exist, no action.                     | {c: 3}                     |


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

Contents of host_vars containing host-specific labels:

    host_labels:
      country: Canada
      province: Quebec
      airport: CSC

Contents of group_vars containing shared group labels:

    group_labels:
      managed_by: Ansible

tests/test.yml:

    - hosts: managed_clusters
      connection: local
      roles:
        - role: ../../ocm-labels
          vars:
            ocm_hub_kubeconfig: "{{ hostvars[groups['hub_cluster'][0]].kubeconfig }}"
            ocm_managedcluster_name: "{{ inventory_hostname }}"
            ocm_merge_type: update
            ocm_user_labels: "{{ hostvars[inventory_hostname].group_labels | combine(hostvars[inventory_hostname].host_labels) }}"

Run the playbook with the inventory specified.

    $ ansible-playbook -i inventory test.yml
