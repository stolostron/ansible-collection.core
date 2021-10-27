ocm-attach
==========

Attaches a managed cluster with an existing hub cluster.


Requirements
------------

The controller must be able to communicate with both the hub and managed cluster.


Environment Variables
---------------------

Environment variables provide the credentials needed by the kubernetes.core collection to connect to the cluster. These variables refer to the managed cluster, ie, the cluster being attached to the hub.

* Option 1, use kubeconfig. Preferred.
* Option 2, use access token.
* Option 3, use username/password. 

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| K8S_AUTH_KUBECONFIG     | yes, Option 1      | ~/.kube/kubeconfig                 | Path to Kubeconfig                       |
| K8S_AUTH_HOST           | yes, Option 2,3    | https://api.cluster.domain.com     | URL to the cluster API                   |
| K8S_AUTH_VERIFY_SSL     | yes, Option 2,3    |                                    | Flag to enforce SSL verification         |
| K8S_AUTH_SSL_CA_CERT    | yes, Option 2,3    |                                    | Path to Certificate Authority            |
| K8S_AUTH_API_KEY        | yes, Option 2      |                                    | Token for a cluster-admin                |
| K8S_AUTH_USERNAME       | yes, Option 3      |                                    | Username for a cluster-admin             |
| K8S_AUTH_PASSWORD       | yes, Option 3      |                                    | Password for a cluster-admin             |


Role Variables
--------------

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_managedcluster_name | yes                | validclustername                   | `^[a-z0-9]([-a-z0-9]*[a-z0-9])?$`        |
| ocm_hub_kubeconfig      | yes                | /path/to/hub_kubeconfig            | Path to the hub's kubeconfig             |
| ocm_klusterlet_version  | no                 | 2.2.0                              | Klusterlet version                       |
| ocm_hub_only            | no                 | false                              | Only setup the cluster entry in the hub  |


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

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      environment:
        K8S_AUTH_KUBECONFIG: /path/to/spoke_kubeconfig
      roles:
        - role: ocm-attach
          vars:
            ocm_managedcluster_name: valid-cluster-name
            ocm_hub_kubeconfig: /path/to/hub_kubeconfig
