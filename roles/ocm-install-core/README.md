ocm-install-core
================

Installs Red Hat Advanced Cluster Management Operator with the MultiClusterHub (MCH).


Requirements
------------

The hosting cluster must be able to connect to an Operator Catalog that contains Red Hat Advanced Cluster Management as well as the image registries to support it.

Disconnected installs are possible provided that images are mirrored internally and then overriding the ocm_install_catalog* variables.


Environment Variables
---------------------

Environment variables provide the credentials needed by the kubernetes.core collection to connect to the cluster.

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

1. Ensure that the above python modules and collections are available.
2. Ensure the kubeconfig for the target cluster(s) are available.
3. Then run the test.yml under the tests directory.

tests/test.yml:

    - hosts: servers
      environment:
        K8S_AUTH_KUBECONFIG: /path/to/kubeconfig
      roles:
        - role: ocm-install-core
          vars:
            ocm_install_catalog: internal-operators-catalog
            ocm_install_catalog_ns: internal-operators
            ocm_version: 2.4.0
            ocm_channel: release-2.4
