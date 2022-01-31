#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managed_serviceaccount_addon

short_description: cluster proxy addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use the managed-serviceaccount addon to setup a serviceaccount on a managedcluster,
    and return the serviceaccount token.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    wait:
        description: Whether to wait for clusters to show up as managed clusters.
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the addons to show up.
        type: int
        default: 60
        required: False
    managed_cluster:
        description: Name of managed cluster to create serviceaccount.
        type: str
        required: True
'''

EXAMPLES = r'''
- name: "Get serviceaccount token"
  ocmplus.cm.managed_serviceaccount_addon:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    wait: True
    timeout: 60
  register: managed_serviceaccount
'''

RETURN = r'''
managed_serviceaccount:
    description: Managed ServiceAccount information
    returned: when cluster proxy is enabled and available
    type: dict
    contains:
      name:
        description: The name of the managed ServiceAccount resource
        type: str
      namespace:
        description: The namespace of the managed ServiceAccount resource
        type: str
      api_version:
        description: The api_version of the managed ServiceAccount resource
        type: str
      kind:
        description: The kind of the managed ServiceAccount resource
        type: str
      uid:
        description: The uuid of the managed ServiceAccount resource
        type: str
      service_account:
        description: ServiceAccount information
        type: dict
        contains:
          name:
            description: The name of the ServiceAccount on managed cluster
            type: str
          namespace:
            description: The namespace of the ServiceAccount on managed cluster
            type: str
          token:
            description: The token of the ServiceAccount
            type: str
    sample: {"name": "na...", "namespace": "na...", "api_version": "authentication.open-cluster-management.io/v1alpha1", "kind": "ManagedServiceAccount", 
             "uid": "ui...", "service_account": {"name": "na...", "namespace": "na...", "token": "ey..."}}
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import base64
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    check_addon_available,
    get_managed_cluster_addon,
    wait_for_addon_available,
    ensure_managed_cluster_addon_enabled,
    generate_random_string,
)

IMP_ERR = {}
try:
    import yaml
except ImportError as e:
    IMP_ERR['yaml'] = {'error': traceback.format_exc(),
                       'exception': e}
try:
    from jinja2 import Template
except ImportError as e:
    IMP_ERR['jinja2'] = {'error': traceback.format_exc(),
                         'exception': e}
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


MANAGED_SERVICE_ACCOUNT_TEMPLATE = """
apiVersion: authentication.open-cluster-management.io/v1alpha1
kind: ManagedServiceAccount
metadata:
  name: cluster-proxy-{{ random_string }}
  namespace: {{ cluster_name }}
spec:
  projected:
    type: None
  rotation: {}
"""


def ensure_managed_service_account_feature_enabled(hub_client):
    # NOTE: managed service account is not a supported feature in ACM yet and it's currently a upstream proposed feature
    #       for more information see https://github.com/open-cluster-management-io/enhancements/pull/24
    # TODO: the code currently only check if managed-serviceaccount feature is enabled
    #  it does not enable the feature yet this code will need to be updated when the feature become officially part of
    #  ACM

    cluster_management_addon_api = hub_client.resources.get(
        api_version='addon.open-cluster-management.io/v1alpha1',
        kind='ClusterManagementAddOn',
    )

    return cluster_management_addon_api.get(name='managed-serviceaccount')


def get_hub_serviceaccount_secret(hub_client, managed_service_account):
    secret_api = hub_client.resources.get(
        api_version='v1',
        kind='Secret',
    )
    secret_name = managed_service_account.metadata.name
    if managed_service_account.tokenSecretRef is not None and managed_service_account.tokenSecretRef.name != '':
        secret_name = managed_service_account.tokenSecretRef.name

    secret = None
    try:
        secret = secret_api.get(
            name=secret_name,
            namespace=managed_service_account.metadata.namespace
        )
    except NotFoundError:
        return None
    return secret


def wait_for_serviceaccount_secret(module: AnsibleModule, hub_client, managed_service_account, timeout=60):
    managed_service_account_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    for event in managed_service_account_api.watch(namespace=managed_service_account.metadata.namespace, timeout=timeout):
        if event['type'] in ['ADDED', 'MODIFIED'] and event['object'].metadata.name == managed_service_account.metadata.name:
            if 'status' in event['object'].keys():
                conditions = event['object']['status'].get('conditions', [])
                for condition in conditions:
                    if condition['type'] == 'SecretCreated' and condition['status'] == 'True':
                        return True

    return False


def ensure_managed_service_account(module: AnsibleModule, hub_client, managed_service_account_addon):
    if 'jinja2' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('jinja2'),
                         exception=IMP_ERR['jinja2']['exception'])
    if 'yaml' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('yaml'),
                         exception=IMP_ERR['yaml']['exception'])
    managed_cluster_name = managed_service_account_addon.metadata.namespace

    managed_service_account_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    new_managed_service_account_raw = Template(MANAGED_SERVICE_ACCOUNT_TEMPLATE).render(
        cluster_name=managed_cluster_name,
        random_string=generate_random_string(),
    )
    managed_service_account_yaml = yaml.safe_load(
        new_managed_service_account_raw)
    managed_service_account = managed_service_account_api.create(
        managed_service_account_yaml)

    return managed_service_account


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    managed_cluster_name = module.params['managed_cluster']

    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )

    managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
    if managed_cluster is None:
        # TODO: throw error and exit
        module.fail_json(
            msg=f'failed to get managedcluster {managed_cluster_name}')
        # TODO: there might be other exit condition

    ensure_managed_service_account_feature_enabled(hub_client)

    ensure_managed_cluster_addon_enabled(
        module, hub_client, 'managed-serviceaccount', managed_cluster_name)

    managed_service_account_addon = get_managed_cluster_addon(
        hub_client, 'managed-serviceaccount', managed_cluster_name)
    wait = module.params['wait']
    timeout = module.params['timeout']
    if timeout is None or timeout <= 0:
        timeout = 60
    if wait:
        wait_for_addon_available(
            module, hub_client, managed_service_account_addon, timeout)

    if not check_addon_available(hub_client, 'managed-serviceaccount', managed_cluster_name):
        module.fail_json(
            msg=f'failed to check addon: addon managed-serviceaccount of {managed_cluster_name} is not available')

    managed_service_account = ensure_managed_service_account(
        module, hub_client, managed_service_account_addon)

    # wait service account secret
    if wait:
        wait_for_serviceaccount_secret(
            module, hub_client, managed_service_account, timeout)

    # grab secret
    secret = get_hub_serviceaccount_secret(hub_client, managed_service_account)
    if secret is None:
        module.fail_json(
            msg=f'failed to get secret: secret of managedserviceaccount {managed_service_account.metadata.name} of cluster {managed_cluster_name} is not found')

    # get token
    token_bytes = base64.b64decode(secret.data.token)
    token = token_bytes.decode('ascii')
    managed_serviceaccount = {'name': managed_service_account.metadata.name, 'namespace': managed_service_account.metadata.namespace,
                              'api_version': managed_service_account.apiVersion, 'kind': managed_service_account.kind, 'uid': managed_service_account.metadata.uid,
                              'service_account': {'name': managed_service_account.metadata.name, 'namespace': managed_service_account_addon.spec.installNamespace, 'token': token}}
    module.exit_json(managed_serviceaccount=managed_serviceaccount)


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
