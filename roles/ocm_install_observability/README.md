ocm_install_observability
=========================

Extends existing Red Hat Advanced Cluster Management (RHACM) Hub with the Observability (MCO) component.


Requirements
------------

RHACM Operator and MultiClusterHub should have been installed already. This role extends RHACM with the Observability component.

Object storage is required to store the metrics. This store needs to be accessible from the hub cluster.

Disconnected installs are possible provided that the images are mirrored internally.


Role Variables
--------------

| Variable                | Required           | Default                            | Comments                                 |
|-------------------------|--------------------|------------------------------------|------------------------------------------|
| ocm_hub_kubeconfig      | yes                |                                    | Path to kubeconfig for the hub           |
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
        - role: ../../ocm_install_observability
          vars:
            ocm_hub_kubeconfig: "{{ hostvars[inventory_hostname].kubeconfig }}"
            ocm_s3_endpoint: cloudstorage.acmecloud.com
            ocm_s3_bucket: bucket4metrics
            ocm_s3_access_key: ABCDE12345abcde
            ocm_s3_secret_key: abcde12345fghij67890
