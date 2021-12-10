Integration Tests for import-eks
================

Imports an existing Amazon Elastic Kubernetes Service (EKS) Cluster into an existing Red Hat Advanced Cluster Management Hub Cluster as a Managed Cluster.


Requirements
------------

An existing Amazon Elastic Kubernetes Service (EKS) Cluster.

An existing Red Hat Advanced Cluster Management Hub Cluster.

Role Variables
--------------

| Variable                   | Required | Default     | Comments                                                                               |
|----------------------------|----------|-------------|----------------------------------------------------------------------------------------|
| eks_cluster_name           | yes      |             | Name of the EKS cluster to be imported                                                 |
| hub_kubeconfig             | yes      |             | Path to the kubeconfig of the RHACM Hub Cluster                                        |
| wait                       | no       | False       | Waits until imported EKS cluster comes online an a managed cluster                     |
| timeout                    | no       | 60          | Number of seconds to wait until imported EKS cluster comes online an a managed cluster |
| addons                     | no       | (see below) | List of addons to enable/disable                                                       |
|   policy_controller        | no       | False       | Whether to enable the policy controller                                                |
|   observability_controller | no       | False       | Whether to enable the observability controller                                         |
|   iam_policy_controller    | no       | False       | Whether to enable the IAM policy controller                                            |
|   search_collector         | no       | False       | Whether to enable the search controller                                                |
|   application_manager      | no       | False       | Whether to enable the application manager                                              |
|   cert_policy_controller   | no       | False       | Whether to enable the observability controller                                         |

This module uses the [AWSModule](https://github.com/ansible-collections/amazon.aws/blob/main/plugins/module_utils/core.py), so any variables (such as `aws_access_key` and `aws_secret_key`) used in the AWSModule also applies here.

Dependencies
------------

The python modules *boto*, *boto3*, *botocore*, and *awscli* (listed in `requirements.txt`) provide the connectivity to EKS clusters.

Additional python modules *ansible*, *kuberentes*, *backoff*, *polling*, and *pyyaml* are required and listed in `requirements.txt`.

To run sanity tests, python modules *voluptuous*, *yamllint*, *pycodestyle*, and *pylint* are required and listed in `test-requirements.txt`.

Example Playbook
----------------

An example of how to run this role with a well formed inventory.

Contents of inventory:

    [all:vars]
    aws_access_key=AWS_KEY_ID
    aws_secret_key=AWS_SECRET
    eks_cluster_name=CLUSTER_NAME
    hub_kubeconfig=PATH_TO_KUBECONFIG
    observability_controller=false
    iam_policy_controller=false
    search_collector=false
    application_manager=false
    cert_policy_controller=false

Run the playbook from the project root with the inventory specified.

    $ ansible-playbook tests/integration/targets/import_eks/tasks/main.yml -i tests/integration/targets/import_eks/tasks/inventory
