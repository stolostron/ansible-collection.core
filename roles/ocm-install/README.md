Role Name
=========

Installs Red Hat Advanced Cluster Management Operator with the option to install the Observability feature.

Requirements
------------

The hosting cluster must be able to connect to an Operator Catalog that contains Red Hat Advanced Cluster Management as well as the image registries to support it. Disconnected installs are possible by overriding the ocm_install_catalog* variables.

If observability will be installed, an S3 object store needs to be accessible from the hosting cluster.


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
| ocm_observability       | no                 | false                              | Option to install observability          |
| ocm_s3_endpoint         | for observability  | overrideme.us-west-1.acmecloud.com | S3 Endpoint for Observability/Thanos     |
| ocm_s3_bucket           | for observability  | overrideme                         | S3 Bucket                                |
| ocm_s3_access_key       | for observability  | overrideme                         | S3 Access Key                            |
| ocm_s3_secret_key       | for observability  | overrideme                         | S3 Secret Key                            |


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
        K8S_AUTH_KUBECONFIG: /path/to/kubeconfig
      roles:
         - role: ocm-install
           vars:
             ocm_observability: true
             ocm_s3_endpoint: cloudstorage.acmecloud.com
             ocm_s3_bucket: bucket4metrics
             ocm_s3_access_key: ABCDE12345abcde
             ocm_s3_secret_key: abcde12345fghij67890