from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible_collections.ocmplus.cm.plugins.module_utils import import_utils

from botocore import session
from awscli.customizations.eks.get_token import STSClientFactory, TokenGenerator, TOKEN_EXPIRATION_MINS
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import AWSRetry
import boto3
import polling

# TODO: learn from other module import error handling and come up with an convention
try:
    import botocore
except ImportError:
    pass  # caught by AnsibleAWSModule

import traceback
from ansible.module_utils._text import to_native, to_bytes, to_text

err = None
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import (
        NotFoundError, ResourceNotFoundError, ResourceNotUniqueError, DynamicApiError,
        ConflictError, ForbiddenError, MethodNotAllowedError, BadRequestError,
        KubernetesValidateMissing
    )
    HAS_K8S_MODULE_HELPER = True
    k8s_import_exception = None
except ImportError as e:
    HAS_K8S_MODULE_HELPER = False
    k8s_import_exception = e
    err = traceback.format_exc()



DOCUMENTATION = r'''

module: import_eks

short_description: Import an AWS EKS cluster into an ACM Hub cluster

author:
    - "Crystal Chun (@CrystalChun) <cchun@redhat.com>"
    - "Hao Liu (@TheRealHaoLiu) <haoli@redhat.com>"
    - "Hanqiu Zhang (@hanqiuzh) <hanzhang@redhat.com>"
    - "Tara Gu (@taragu) <tgu@redhat.com>"

description: Import an AWS EKS cluster into an ACM Hub cluster

options:
  eks_cluster_name:
    description: Name of the AWS EKS cluster to import
    type: str
  hub_kubeconfig:
    description: Path to the ACM Hub cluster kubeconfig
    type: str
  aws_access_key:
    description: AWS access key ID
    type: str
  aws_secret_key:
    description: AWS secret key
    type: str
  addons:
    description:
      - List of ACM addons to enable/disable
    type: list
    elements: dict
    suboptions:
      policy_controller:
        type: bool
        description: enable/disable the policy controller addon. This value is required to be True.
        required: yes
      observability_controller:
        type: bool
        description: enable/disable the observability controller addon.
        required: yes
      iam_policy_controller:
        type: bool
        description: enable/disable the IAM policy controller addon.
        required: yes
      search_collector:
        type: bool
        description: enable/disable the search collector addon.
        required: yes
      application_manager:
        type: bool
        description: enable/disable the application manager addon.
        required: yes
      cert_policy_controller:
        type: bool
        description: enable/disable the cert policy controller addon.
        required: yes
'''

EXAMPLES = r'''
- name: "Import EKS cluster"
  ocmplus.cm.import_eks:
    eks_cluster_name: "xxxxx"
    hub_kubeconfig: "/path/to/kubeconfig"
    addons:
      policy_controller: true
      observability_controller: false
      iam_policy_controller: false
      search_collector: false
      application_manager: false
      cert_policy_controller: false
    aws_access_key: xxxx
    aws_secret_key: xxxx
'''

RETURN = r'''
cluster_name:
  description: Name of the EKS cluster imported
  returned: when cluster import succeeds
  type: str
  sample: "cluster_name"
ok:
  description: Whether EKS cluster import succeeds
  return: when cluster import succeeds or fails
  type: bool
  sample: True
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''


def execute_module(module):
    eks_cluster_name = module.params['eks_cluster_name']
    addons = module.params['addons']
    wait = module.params['wait'] # if key exists and no value and watch out for wait package in python
    timeout = module.params['timeout']
    aws_access_key = module.params['aws_access_key']
    aws_secret_key = module.params['aws_secret_key']

    # Create EKS connection
    eks_conn = boto3.client('eks', aws_access_key_id=aws_access_key, aws_secret_access_key=aws_secret_key)

    # Create STS connection
    work_session = session.get_session()
    work_session.set_credentials(aws_access_key, aws_secret_key)
    sts_client = STSClientFactory(work_session).get_sts_client()
    sts_token = TokenGenerator(sts_client).get_token(eks_cluster_name)

    # TODO: validate hub connection and fail early if not hub
    hub_kubeconfig = kubernetes.config.load_kube_config(config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )

    # TODO: handle error if eks cluster does not exist or unable to connect
    eks_kubeconfig = get_eks_kubeconfig(eks_conn, sts_token, eks_cluster_name)
    eks_kubeconfig.verify_ssl = False
    eks_kube_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=eks_kubeconfig)
    )

    managedcluster = import_utils.ensure_managedcluster(hub_client, eks_cluster_name)
    import_utils.ensure_klusterletaddonconfig(hub_client, eks_cluster_name, addons)

    if import_utils.should_import(managedcluster):
        crds_yaml, import_yamls = import_utils.get_import_yamls(hub_client, eks_cluster_name)
        import_utils.dynamic_apply(eks_kube_client, crds_yaml)
        for resource in import_yamls:
            import_utils.dynamic_apply(eks_kube_client, resource)

        if wait:
            managedcluster_api = hub_client.resources.get(
                api_version="cluster.open-cluster-management.io/v1",
                kind="ManagedCluster"
            )

            polling.poll(
                target=lambda: managedcluster_api.get(name=eks_cluster_name),
                check_success=import_utils.should_import,
                step=5,
                timeout=timeout,
            )

    module.exit_json(err=err, cluster_name=eks_cluster_name, ok=True)


def get_eks_kubeconfig(eks_conn,
                       sts_token,
                       eks_cluster_name: str) -> kubernetes.client.Configuration:
    eks_cluster_info = eks_conn.describe_cluster(name=eks_cluster_name)

    eks_kubeconfig = kubernetes.client.Configuration()
    eks_kubeconfig.host = eks_cluster_info['cluster']['endpoint']
    eks_kubeconfig.api_key = {"authorization": "Bearer " + sts_token}

    return eks_kubeconfig


def main():
    # define available arguments/parameters a user can pass to the module
    argument_spec = dict(
        eks_cluster_name=dict(type='str', required=True),
        hub_kubeconfig=dict(type='str', required=True),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60),
        addons=dict(
            type='dict', 
            required=False, 
            options=dict(
                policy_controller=dict(type='bool', required=False, default=False),
                observability_controller=dict(type='bool', required=False, default=False),
                iam_policy_controller=dict(type='bool', required=False, default=False),
                search_collector=dict(type='bool', required=False, default=False),
                application_manager=dict(type='bool', required=False, default=False),
                cert_policy_controller=dict(type='bool', required=False, default=False),
            ),
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    if not HAS_K8S_MODULE_HELPER:
        module.fail_json(
            msg='kubernetes import error',
            exception=err,
            error=to_native(k8s_import_exception)
        )

    execute_module(module)


if __name__ == '__main__':
    main()
