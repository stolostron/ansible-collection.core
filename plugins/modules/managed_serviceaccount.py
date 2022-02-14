#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managed_serviceaccount

short_description: managed serviceaccount

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use the managed-serviceaccount to setup a serviceaccount on a managedcluster,
    and return the serviceaccount token.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    wait:
        description: Whether to wait for managed-serviceaccount to show up.
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the managed-serviceaccount to show up.
        type: int
        default: 60
        required: False
    ttl_seconds_after_creation:
        description:
        - The lifetime of a ManagedServiceAccount in seconds. If set, the ManagedServiceAccount will be automatically deleted.
          If this field is unset, the ManagedServiceAccount won't be automatically deleted.
          If this field is set to zero, the ManagedServiceAccount becomes eligible to be deleted immediately after it creation.
        type: int
        required: False
    managed_cluster:
        description: Name of managed cluster to create serviceaccount.
        type: str
        required: True
    state:
        description:
        - Determines if managed-serviceaccount should be created, or deleted. When set to C(present), an object will be
          created. If set to C(absent), an existing object will be deleted.
        type: str
        default: present
        choices: [ absent, present ]
        required: False
    name:
        description:
        - Name of managed-serviceaccount.
        - Required only if C(state=absent)
        type: str
'''

EXAMPLES = r'''
- name: "Get serviceaccount token"
  ocmplus.cm.managed_serviceaccount:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    wait: True
    timeout: 60
  register: managed_serviceaccount

- name: "Remove an existing managed-serviceaccount object"
  ocmplus.cm.managed_serviceaccount:
    state: absent
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    name: managed-serviceaccount-name
    wait: True
    timeout: 60
'''

RETURN = r'''
managed_serviceaccount:
    description: A dictionary of Managed ServiceAccount information
    returned: only when Managed ServiceAccount addon is enabled and available
    type: complex
    contains:
      name:
        description: Managed ServiceAccount name
        type: str
      managed_cluster:
        description: Managed cluster name
        type: str
      token:
        description: ServiceAccount token
        type: str
    sample: {"name": "na...", "managed_cluster": "ma...", "token": "ey..."}
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import time
import base64
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    check_addon_available,
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
  generateName: {{ cluster_name }}-managed-serviceaccount-
  namespace: {{ cluster_name }}
spec:
  {%- if ttl_seconds %}
  ttlSecondsAfterCreation: {{ ttl_seconds }}
  {%- endif %}
  projected:
    type: None
  rotation: {}
"""


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

    start_time = time.time()
    while time.time() - start_time < timeout:
        for event in managed_service_account_api.watch(namespace=managed_service_account.metadata.namespace, timeout=timeout):
            if event['type'] in ['ADDED', 'MODIFIED'] and event['object'].metadata.name == managed_service_account.metadata.name:
                if 'status' in event['object'].keys():
                    conditions = event['object']['status'].get(
                        'conditions', [])
                    for condition in conditions:
                        if condition['type'] == 'SecretCreated' and condition['status'] == 'True':
                            return True

    return False


def ensure_managed_service_account(module: AnsibleModule, hub_client, managed_cluster_name, ttl_seconds=None):
    if 'jinja2' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('jinja2'),
                         exception=IMP_ERR['jinja2']['exception'])
    if 'yaml' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('yaml'),
                         exception=IMP_ERR['yaml']['exception'])

    managed_service_account_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    render_config = {
        'cluster_name': managed_cluster_name,
    }
    if ttl_seconds:
        render_config['ttl_seconds'] = ttl_seconds

    new_managed_service_account_raw = Template(MANAGED_SERVICE_ACCOUNT_TEMPLATE).render(
        render_config
    )
    managed_service_account_yaml = yaml.safe_load(
        new_managed_service_account_raw)
    managed_service_account = managed_service_account_api.create(
        managed_service_account_yaml)

    return managed_service_account


def get_managed_service_account(hub_client, managed_cluster_name, managed_serviceaccount_name):
    managed_service_account_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    try:
        managed_service_account = managed_service_account_api.get(
            namespace=managed_cluster_name,
            name=managed_serviceaccount_name,
        )
    except NotFoundError:
        managed_service_account = None

    return managed_service_account


def delete_managed_service_account(hub_client, managed_service_account):
    managed_service_account_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    status = managed_service_account_api.delete(
        namespace=managed_service_account.metadata.namespace,
        name=managed_service_account.metadata.name,
    )

    return (status.status == 'Success')


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
    wait = module.params['wait']
    timeout = module.params['timeout']
    ttl_seconds = module.params['ttl_seconds_after_creation']
    if ttl_seconds is not None and ttl_seconds < 0:
        module.fail_json(msg='Expecting ttl_seconds_after_creation >= 0, ' +
                         f'but ttl_seconds_after_creation={ttl_seconds}')
    if timeout is None or timeout <= 0:
        timeout = 60
    state = module.params['state']

    if state == 'present':
        managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
        if managed_cluster is None:
            # TODO: throw error and exit
            module.fail_json(
                msg=f'failed to get managedcluster {managed_cluster_name}')
            # TODO: there might be other exit condition

        addon_name = 'managed-serviceaccount'
        if not check_addon_available(hub_client, managed_cluster_name, addon_name):
            module.fail_json(
                msg=f'failed to check addon: {addon_name} of {managed_cluster_name} is not available')

        managed_service_account = ensure_managed_service_account(
            module, hub_client, managed_cluster_name, ttl_seconds)

        # wait service account secret
        if wait:
            wait_for_serviceaccount_secret(
                module, hub_client, managed_service_account, timeout)

        # grab secret
        secret = get_hub_serviceaccount_secret(
            hub_client, managed_service_account)
        if secret is None:
            msan = managed_service_account.metadata.name
            mcn = managed_cluster_name
            module.fail_json(
                msg=f'failed to get secret: secret of managedserviceaccount {msan} of cluster {mcn} is not found')

        # get token
        token_bytes = base64.b64decode(secret.data.token)
        token = token_bytes.decode('ascii')
        managed_serviceaccount = {
            'name': managed_service_account.metadata.name,
            'managed_cluster': managed_cluster_name,
            'token': token,
        }
        module.exit_json(
            changed=True, managed_serviceaccount=managed_serviceaccount)
    elif state == 'absent':
        managed_serviceaccount_name = module.params['name']
        managed_serviceaccount = {
            'name': managed_serviceaccount_name,
            'managed_cluster': managed_cluster_name,
            'token': None,
        }
        managed_service_account = get_managed_service_account(
            hub_client, managed_cluster_name, managed_serviceaccount_name)
        if managed_service_account is None:
            module.exit_json(
                changed=False, managed_serviceaccount=managed_serviceaccount)
        if delete_managed_service_account(hub_client, managed_service_account):
            module.exit_json(
                changed=True, managed_serviceaccount=managed_serviceaccount)
        else:
            module.fail_json(
                msg=f'Error deleting managed-serviceaccount {managed_serviceaccount_name}')


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60),
        state=dict(
            type="str", default="present", choices=["present", "absent"]
        ),
        name=dict(type='str'),
        ttl_seconds_after_creation=dict(type='int', required=False)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ("state", "absent", ["name"]),
        ],
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
