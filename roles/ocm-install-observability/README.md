ocm-install-observability
=========================

Extends existing Red Hat Advanced Cluster Management (RHACM) Hub with the Observability (MCO) component.


Requirements
------------

RHACM Operator and MultiClusterHub should have been installed already. This role extends RHACM with the Observability component.

Object storage is required to store the metrics. This store needs to be accessible from the hub cluster.

Disconnected installs are possible provided that the images are mirrored internally.


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
| ocm_s3_endpoint         | yes                | overrideme.us-west-1.acmecloud.com | S3 Endpoint for Observability/Thanos     |
| ocm_s3_bucket           | yes                | overrideme                         | S3 Bucket                                |
| ocm_s3_access_key       | yes                | overrideme                         | S3 Access Key                            |
| ocm_s3_secret_key       | yes                | overrideme                         | S3 Secret Key                            |


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
        - role: ocm-install-observability
          vars:
            ocm_s3_endpoint: cloudstorage.acmecloud.com
            ocm_s3_bucket: bucket4metrics
            ocm_s3_access_key: ABCDE12345abcde
            ocm_s3_secret_key: abcde12345fghij67890
