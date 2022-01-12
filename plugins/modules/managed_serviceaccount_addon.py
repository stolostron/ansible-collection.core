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

description:
- Use the managed-serviceaccount addon to setup a serviceaccount on a managedcluster with default admin permission,
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
  register: token
'''

RETURN = r'''
token:
    description: token of the specific serviceaccount
    returned: when cluster proxy is enabled and available
    type: str
    sample: "ey..."
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import base64
import traceback

from ansible.errors import AnsibleError
from ansible.module_utils.basic import AnsibleModule, env_fallback
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    check_addon_available,
    get_managed_cluster_addon,
    wait_for_addon_available
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
    import polling
except ImportError as e:
    IMP_ERR['polling'] = {'error': traceback.format_exc(), 'exception': e}

try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    # kubernetes are always used, so if cannot be imported, will raise error directly
    raise AnsibleError("Error importing Kubernetes: " + e) from e

SERVICE_ACCOUNT_MANIFEST_WORK_TEMPLATE = """
apiVersion: work.open-cluster-management.io/v1
kind: ManifestWork
metadata:
  name: {{ service_account_name }}.serviceaccount
  namespace: {{ cluster_name }}
spec:
  workload:
    manifests:
    - apiVersion: v1
      kind: ServiceAccount
      metadata:
        name: {{ service_account_name }}
        namespace: {{ service_account_namespace }}
    - apiVersion: v1
      kind: Secret
      metadata:
        name: {{ service_account_name }}
        namespace: {{ service_account_namespace }}
        annotations:
          kubernetes.io/service-account.name: {{ service_account_name }}
      type: kubernetes.io/service-account-token
    - apiVersion: rbac.authorization.k8s.io/v1
      kind: ClusterRoleBinding
      metadata:
        name: {{ service_account_name }}
      roleRef:
        apiGroup: rbac.authorization.k8s.io
        kind: ClusterRole
        name: cluster-admin
      subjects:
        - kind: ServiceAccount
          name: {{ service_account_name }}
          namespace: {{ service_account_namespace }}
"""

MANAGED_SERVICE_ACCOUNT_TEMPLATE = """
apiVersion: authentication.open-cluster-management.io/v1alpha1
kind: ManagedServiceAccount
metadata:
  name: cluster-proxy
  namespace: {{ cluster_name }}
spec:
  projected:
    type: None
  rotation: {}
"""

MANAGED_SERVICE_ACCOUNT_CLUSTER_ROLE_BINDING_TEMPLATE = """
apiVersion: work.open-cluster-management.io/v1
kind: ManifestWork
metadata:
  name: {{ managed_service_account_name }}.cluster-role-binding
  namespace: {{ cluster_name }}
spec:
  workload:
    manifests:
    - apiVersion: rbac.authorization.k8s.io/v1
      kind: ClusterRoleBinding
      metadata:
        name: {{ managed_service_account_name }}
      roleRef:
        apiGroup: rbac.authorization.k8s.io
        kind: ClusterRole
        name: cluster-admin
      subjects:
        - kind: ServiceAccount
          name: {{ managed_service_account_name }}
          namespace: {{ managed_service_account_namespace }}
"""


def ensure_managed_service_account_feature_enabled(hub_client: kubernetes.dynamic.DynamicClient):
    # NOTE: managed service account is not a supported feature in ACM yet and it's currently a upstream proposed feature
    #       for more information see https://github.com/open-cluster-management-io/enhancements/pull/24
    # TODO: the code currently only check if managed-serviceaccount feature is enabled
    #  it does not enable the feature yet this code will need to be updated when the feature become officially part of
    #  ACM

    cluster_management_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ClusterManagementAddOn",
    )

    return cluster_management_addon_api.get(name='managed-serviceaccount')


def get_hub_serviceaccount_secret(hub_client: kubernetes.dynamic.DynamicClient, managed_service_account):
    secret_api = hub_client.resources.get(
        api_version="v1",
        kind="Secret",
    )
    secret_name = managed_service_account.metadata.name
    if managed_service_account.tokenSecretRef is not None and managed_service_account.tokenSecretRef.name != "":
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


def wait_for_serviceaccount_secret(hub_client: kubernetes.dynamic.DynamicClient, managed_service_account, timeout=60):
    if 'polling' in IMP_ERR:
        raise AnsibleError("Error importing polling: " + IMP_ERR['polling']['error']) from None

    managed_service_account_api = hub_client.resources.get(
        api_version="authentication.open-cluster-management.io/v1alpha1",
        kind="ManagedServiceAccount",
    )

    def check_success(response) -> bool:
        if response is None:
            return False
        for condition in response['status']['conditions']:
            if condition['type'] == 'SecretCreated':
                return condition['status'] == 'True'
        return False

    is_available = polling.poll(
        target=lambda: managed_service_account_api.get(
            name=managed_service_account.metadata.name,
            namespace=managed_service_account.metadata.namespace
        ),
        check_success=check_success,
        step=0.1,
        timeout=timeout,
    )

    return is_available


def ensure_managed_service_account(hub_client: kubernetes.dynamic.DynamicClient, managed_service_account_addon):
    if 'jinja2' in IMP_ERR:
        raise AnsibleError("Error importing jinja2: " + IMP_ERR['jinja2']['error']) from None
    if 'yaml' in IMP_ERR:
        raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error']) from None
    managed_cluster_name = managed_service_account_addon.metadata.namespace
    managed_cluster_namespace = managed_service_account_addon.metadata.namespace

    managed_service_account_api = hub_client.resources.get(
        api_version="authentication.open-cluster-management.io/v1alpha1",
        kind="ManagedServiceAccount",
    )

    try:
        managed_service_account = managed_service_account_api.get(
            name='cluster-proxy',
            namespace=managed_cluster_namespace,
        )
    except NotFoundError:
        new_managed_service_account_raw = Template(MANAGED_SERVICE_ACCOUNT_TEMPLATE).render(
            cluster_name=managed_cluster_name,
        )
        managed_service_account_yaml = yaml.safe_load(
            new_managed_service_account_raw)
        managed_service_account = managed_service_account_api.create(
            managed_service_account_yaml)

    return managed_service_account


def ensure_managed_service_account_rbac(hub_client, managed_service_account, managed_service_account_addon):
    if 'jinja2' in IMP_ERR:
        raise AnsibleError("Error importing jinja2: " + IMP_ERR['jinja2']['error']) from None
    if 'yaml' in IMP_ERR:
        raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error']) from None
    managed_cluster_name = managed_service_account_addon.metadata.namespace
    managed_service_account_name = managed_service_account.metadata.name
    managed_service_account_namespace = managed_service_account_addon.spec.installNamespace

    manifest_work_api = hub_client.resources.get(
        api_version="work.open-cluster-management.io/v1",
        kind="ManifestWork",
    )

    new_manifest_work_raw = Template(MANAGED_SERVICE_ACCOUNT_CLUSTER_ROLE_BINDING_TEMPLATE).render(
        cluster_name=managed_cluster_name,
        managed_service_account_name=managed_service_account_name,
        managed_service_account_namespace=managed_service_account_namespace,
    )

    new_manifest_work = yaml.safe_load(new_manifest_work_raw)

    try:
        manifest_work = manifest_work_api.get(
            name=new_manifest_work['metadata']['name'],
            namespace=new_manifest_work['metadata']['namespace'],
        )
        # TODO: validate existing service_account_manifest_work and verify that it is what we expected update if not
    except NotFoundError:
        manifest_work = manifest_work_api.create(new_manifest_work)
        # TODO: we may need to wait for the manifest work to be applied

    return manifest_work


def execute_module(module: AnsibleModule):
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
            err=f'failed to get managedcluster {managed_cluster_name}')
        # TODO: there might be other exit condition

    ensure_managed_service_account_feature_enabled(hub_client)

    managed_service_account_addon = get_managed_cluster_addon(
        hub_client, "managed-serviceaccount", managed_cluster_name)
    wait = module.params['wait']
    timeout = module.params['timeout']
    if timeout is None or timeout <= 0:
        timeout = 60
    if wait:
        wait_for_addon_available(
            hub_client, managed_service_account_addon, timeout)

    if not check_addon_available(hub_client, "managed-serviceaccount", managed_cluster_name):
        module.fail_json(
            err=f'failed to check addon: addon managed-serviceaccount of {managed_cluster_name} is not available')

    managed_service_account = ensure_managed_service_account(
        hub_client, managed_service_account_addon)
    ensure_managed_service_account_rbac(
        hub_client, managed_service_account, managed_service_account_addon)

    # wait service account secret
    if wait:
        wait_for_serviceaccount_secret(
            hub_client, managed_service_account, timeout)
    managed_service_account = ensure_managed_service_account(
        hub_client, managed_service_account_addon)

    # grab secret
    secret = get_hub_serviceaccount_secret(hub_client, managed_service_account)
    if secret is None:
        module.fail_json(
            err=f'failed to get secret: secret of managedserviceaccount {managed_service_account.metadata.name} of cluster {managed_cluster_name} is not found')

    # get token
    token_bytes = base64.b64decode(secret.data.token)
    token = token_bytes.decode('ascii')
    module.exit_json(token=token)


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(env_fallback, ['K8S_AUTH_KUBECONFIG'])),
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
