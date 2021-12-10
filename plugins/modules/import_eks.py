#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type


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
    required: yes
  hub_kubeconfig:
    description: Path to the ACM Hub cluster kubeconfig
    type: str
    required: yes
  wait:
    description: Whether to wait for clusters to show up as managed clusters
    type: bool
    default: False
    required: no
  timeout:
    description: Number of seconds to wait for clusters to show up as managed clusters
    type: int
    default: 60
    required: no
  addons:
    description:
      - List of ACM addons to enable/disable
    type: dict
    required: no
    suboptions:
      policy_controller:
        type: bool
        description: enable/disable the policy controller addon. This value is required to be True.
        required: no
        default: False
      observability_controller:
        type: bool
        description: enable/disable the observability controller addon.
        required: no
        default: False
      iam_policy_controller:
        type: bool
        description: enable/disable the IAM policy controller addon.
        required: no
        default: False
      search_collector:
        type: bool
        description: enable/disable the search collector addon.
        required: no
        default: False
      application_manager:
        type: bool
        description: enable/disable the application manager addon.
        required: no
        default: False
      cert_policy_controller:
        type: bool
        description: enable/disable the cert policy controller addon.
        required: no
        default: False
  debug_botocore_endpoint_logs:
    description:
      - Use a botocore.endpoint logger to parse the unique (rather than total) "resource:action" API calls made during a task, outputing
        the set to the resource_actions key in the task results. Use the aws_resource_action callback to output to total list made during
        a playbook. The ANSIBLE_DEBUG_BOTOCORE_LOGS environment variable may also be used.
    type: bool
    default: 'no'
  validate_certs:
    description:
      - When set to "no", SSL certificates will not be validated for
        communication with the AWS APIs.
    type: bool
    default: yes
  ec2_url:
    description:
      - URL to use to connect to EC2 or your Eucalyptus cloud (by default the module will use EC2 endpoints).
        Ignored for modules where region is required. Must be specified for all other modules if region is not used.
        If not set then the value of the EC2_URL environment variable, if any, is used.
    type: str
    aliases: [ aws_endpoint_url, endpoint_url ]
  aws_secret_key:
    description:
      - C(AWS secret key). If not set then the value of the C(AWS_SECRET_ACCESS_KEY), C(AWS_SECRET_KEY), or C(EC2_SECRET_KEY) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_secret_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_secret_key, secret_key ]
  aws_access_key:
    description:
      - C(AWS access key). If not set then the value of the C(AWS_ACCESS_KEY_ID), C(AWS_ACCESS_KEY) or C(EC2_ACCESS_KEY) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(aws_access_key) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ ec2_access_key, access_key ]
  security_token:
    description:
      - C(AWS STS security token). If not set then the value of the C(AWS_SECURITY_TOKEN) or C(EC2_SECURITY_TOKEN) environment variable is used.
      - If I(profile) is set this parameter is ignored.
      - Passing the I(security_token) and I(profile) options at the same time has been deprecated
        and the options will be made mutually exclusive after 2022-06-01.
    type: str
    aliases: [ aws_security_token, access_token ]
  profile:
    description:
      - Using I(profile) will override I(aws_access_key), I(aws_secret_key) and I(security_token)
        and support for passing them at the same time as I(profile) has been deprecated.
      - I(aws_access_key), I(aws_secret_key) and I(security_token) will be made mutually exclusive with I(profile) after 2022-06-01.
    type: str
    aliases: [ aws_profile ]
  aws_config:
    description:
      - A dictionary to modify the botocore configuration.
      - Parameters can be found at U(https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore.config.Config).
      - Only the 'user_agent' key is used for boto modules. See U(http://boto.cloudhackers.com/en/latest/boto_config_tut.html#boto) for more boto configuration.
    type: dict
  aws_ca_bundle:
    description:
      - "The location of a CA Bundle to use when validating SSL certificates."
      - "Not used by boto 2 based modules."
      - "Note: The CA Bundle is read 'module' side and may need to be explicitly copied from the controller if not run locally."
    type: path
  region:
        description:
          - The AWS region to use. If not specified then the value of the AWS_REGION or EC2_REGION environment variable, if any, is used.
            See U(http://docs.aws.amazon.com/general/latest/gr/rande.html#ec2_region)
        type: str
        aliases: [ aws_region, ec2_region ]
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
  returned: when cluster import succeeds or fails
  type: bool
  sample: True
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''


import logging
import traceback
IMP_ERR = {}
try:
    import boto3
    from botocore import session
except ImportError as e:
    IMP_ERR['boto'] = {'error': traceback.format_exc(),
                       'exception': e}
try:
    import kubernetes
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}
from ansible.errors import AnsibleError
from ansible.module_utils.basic import missing_required_lib, to_native
from ansible_collections.ocmplus.cm.plugins.module_utils import import_utils
from ansible_collections.amazon.aws.plugins.module_utils.core import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.ec2 import get_aws_connection_info

try:
    from awscli.customizations.eks.get_token import STSClientFactory, TokenGenerator
except ImportError as e:
    IMP_ERR['awscli'] = {'error': traceback.format_exc(),
                         'exception': e}


def check_module_import(module):
    if IMP_ERR:
        for k, v in IMP_ERR.items():
            module.fail_json(msg=missing_required_lib(k), exception=v['exception'],
                             error=to_native(v['error']))


def execute_module(module):
    check_module_import(module)
    eks_cluster_name = module.params['eks_cluster_name']
    addons = module.params['addons']
    # If key exists and no value and watch out for wait package in python
    wait = module.params['wait']
    timeout = module.params['timeout']

    aws_connect_kwargs = get_aws_connection_info(module, boto3=True)[2]
    aws_access_key = aws_connect_kwargs['aws_access_key_id']
    aws_secret_key = aws_connect_kwargs['aws_secret_access_key']

    # Create EKS connection
    eks_conn = boto3.client('eks',
                            aws_access_key_id=aws_access_key,
                            aws_secret_access_key=aws_secret_key)

    # Create STS connection
    work_session = session.get_session()
    work_session.set_credentials(aws_access_key, aws_secret_key)
    sts_client = STSClientFactory(work_session).get_sts_client()
    sts_token = TokenGenerator(sts_client).get_token(eks_cluster_name)

    # TODO: validate hub connection and fail early if not hub
    # The Hub kubeconfig is loaded onto kubernetes.client.Configuration
    kubernetes.config.load_kube_config(config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient()
    )

    # TODO: handle error if eks cluster does not exist or unable to connect
    eks_kubeconfig = get_eks_kubeconfig(eks_conn, sts_token, eks_cluster_name)
    eks_kubeconfig.verify_ssl = False
    eks_kube_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=eks_kubeconfig)
    )

    try:
        managedcluster = import_utils.ensure_managedcluster(hub_client, eks_cluster_name)
        import_utils.ensure_klusterletaddonconfig(hub_client, eks_cluster_name, addons)
        if import_utils.should_import(managedcluster):
            crds_yaml, import_yamls = import_utils.get_import_yamls(hub_client, eks_cluster_name)
            try:
                import_utils.dynamic_apply(eks_kube_client, crds_yaml)
            except AnsibleError as e:
                logging.error("Error when applying CRD yamls: %s", traceback.format_exc())
            for resource in import_yamls:
                try:
                    import_utils.dynamic_apply(eks_kube_client, resource)
                except AnsibleError:
                    logging.error("Error when applying import yamls: %s", traceback.format_exc())

            if wait:
                managedcluster_api = hub_client.resources.get(
                    api_version="cluster.open-cluster-management.io/v1",
                    kind="ManagedCluster"
                )
                try:
                    import polling
                    polling.poll(
                        target=lambda: managedcluster_api.get(name=eks_cluster_name),
                        check_success=import_utils.should_import,
                        step=5,
                        timeout=timeout,
                    )
                except ImportError as e:
                    module.fail_json(msg=missing_required_lib('polling'), exception=e,
                                     error=to_native(traceback.format_exc()))
    except AnsibleError as e:
        module.fail_json(err=str(e))

    module.exit_json(cluster_name=eks_cluster_name, ok=True)


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
            options=dict(
                policy_controller=dict(type='bool', default=False),
                observability_controller=dict(type='bool', default=False),
                iam_policy_controller=dict(type='bool', default=False),
                search_collector=dict(type='bool', default=False),
                application_manager=dict(type='bool', default=False),
                cert_policy_controller=dict(type='bool', default=False),
            ),
            default={},
        ),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    execute_module(module)


if __name__ == '__main__':
    main()
