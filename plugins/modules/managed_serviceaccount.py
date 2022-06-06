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
    state:
        description:
        - Determines if managed-serviceaccount should be created, or deleted. When set to C(present), an object will be
          created. If set to C(absent), an existing object will be deleted.
        type: str
        default: present
        choices: [ absent, present ]
        required: False
    managed_cluster:
        description: Name of managed cluster to create serviceaccount.
        type: str
        required: True
    name:
        description:
        - This field specify the name of managed-serviceaccount.
        - The name must be unique for a specific managed-cluster.
        - Use this field for persistent and long lived managed-serviceaccount.
        - Consider using generate_name if the managed-serviceaccount is temporary to avoid collision between playbooks.
        - Required if C(state=absent)
        type: str
    generate_name:
        description:
        - This field is a prefix used to generate a unique name if the name field has not been provided.
        - If this field is used the value will be combined with a unique suffix.
        - The provided value has the same validation rules as the name field and may truncate by the length of the
          suffix required to make the value unique.
        - Consider using this field with ttl_seconds_after_creation to avoid accumulation of managed-serviceaccount objects.
        type: str
    ttl_seconds_after_creation:
        description:
        - The lifetime of a ManagedServiceAccount in seconds.
          If set, the ManagedServiceAccount will be automatically deleted.
          If this field is unset, the ManagedServiceAccount won't be automatically deleted.
          If this field is set to zero, the ManagedServiceAccount will be deleted immediately after it creation.
        type: int
        required: False
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
'''

EXAMPLES = r'''
- name: "Get serviceaccount token"
  stolostron.core.managed_serviceaccount:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    wait: True
    timeout: 60
  register: managed_serviceaccount

- name: "Remove an existing managed-serviceaccount object"
  stolostron.core.managed_serviceaccount:
    state: absent
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    name: managed-serviceaccount-name
    wait: True
    timeout: 60
'''

RETURN = r'''
msg:
    description: human readable message describing the managed serviceaccount is ready or not.
    returned: always
    type: str
name:
    description: Managed ServiceAccount name
    returned: success
    type: str
managed_cluster:
    description: Managed cluster name
    returned: success
    type: str
token:
    description: ServiceAccount token
    returned: success
    type: str
exception:
    description: exception catched during the process.
    returned: when exception is catched
    type: complex
    contains: {}
'''

import time
import base64
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.stolostron.core.plugins.module_utils.addon_utils import check_addon_available

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


MANAGED_SERVICEACCOUNT_TEMPLATE = """
apiVersion: authentication.open-cluster-management.io/v1alpha1
kind: ManagedServiceAccount
metadata:
{%- if name %}
  name: {{ name }}
{%- else %}
  generateName: {{ generate_name | default("") }}
{%- endif %}
  namespace: {{ managed_cluster }}
spec:
  {%- if ttl_seconds_after_creation %}
  ttlSecondsAfterCreation: {{ ttl_seconds_after_creation }}
  {%- endif %}
  rotation: {}
"""


def get_hub_serviceaccount_secret(hub_client, managed_serviceaccount):
    secret_api = hub_client.resources.get(
        api_version='v1',
        kind='Secret',
    )
    secret_name = managed_serviceaccount.metadata.name
    if managed_serviceaccount.tokenSecretRef is not None and managed_serviceaccount.tokenSecretRef.name != '':
        secret_name = managed_serviceaccount.tokenSecretRef.name

    secret = None
    try:
        secret = secret_api.get(
            name=secret_name,
            namespace=managed_serviceaccount.metadata.namespace
        )
    except NotFoundError:
        return None

    return secret


def wait_for_serviceaccount_secret(module: AnsibleModule, hub_client, managed_serviceaccount, timeout=60):
    managed_serviceaccount_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    start_time = time.time()
    while time.time() - start_time < timeout:
        for event in managed_serviceaccount_api.watch(namespace=managed_serviceaccount.metadata.namespace, timeout=timeout):
            if event['type'] in ['ADDED', 'MODIFIED'] and event['object'].metadata.name == managed_serviceaccount.metadata.name:
                if 'status' in event['object'].keys():
                    conditions = event['object']['status'].get(
                        'conditions', [])
                    for condition in conditions:
                        if condition['type'] == 'SecretCreated' and condition['status'] == 'True':
                            return True

    return False


def ensure_managed_serviceaccount(module: AnsibleModule, hub_client, managed_cluster_name, ttl_seconds=None):
    if 'jinja2' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('jinja2'),
                         exception=IMP_ERR['jinja2']['exception'])
    if 'yaml' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('yaml'),
                         exception=IMP_ERR['yaml']['exception'])

    managed_serviceaccount_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    managed_serviceaccount = None

    if module.params['name']:
        managed_serviceaccount = get_managed_serviceaccount(
            hub_client,
            module.params['managed_cluster'],
            module.params['name'],
        )

    new_managed_serviceaccount_raw = Template(
        MANAGED_SERVICEACCOUNT_TEMPLATE).render(module.params)
    managed_serviceaccount_yaml = yaml.safe_load(
        new_managed_serviceaccount_raw)

    if managed_serviceaccount is None:
        managed_serviceaccount = managed_serviceaccount_api.create(
            managed_serviceaccount_yaml)
    else:
        managed_serviceaccount = managed_serviceaccount_api.patch(
            name=module.params['name'],
            namespace=module.params['managed_cluster'],
            body=managed_serviceaccount_yaml,
            content_type="application/merge-patch+json",
        )

    return managed_serviceaccount


def get_managed_serviceaccount(hub_client, managed_cluster_name, managed_serviceaccount_name):
    managed_serviceaccount_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    try:
        managed_serviceaccount = managed_serviceaccount_api.get(
            namespace=managed_cluster_name,
            name=managed_serviceaccount_name,
        )
    except NotFoundError:
        managed_serviceaccount = None

    return managed_serviceaccount


def delete_managed_serviceaccount(hub_client, managed_serviceaccount):
    managed_serviceaccount_api = hub_client.resources.get(
        api_version='authentication.open-cluster-management.io/v1alpha1',
        kind='ManagedServiceAccount',
    )

    status = managed_serviceaccount_api.delete(
        namespace=managed_serviceaccount.metadata.namespace,
        name=managed_serviceaccount.metadata.name,
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

        managed_serviceaccount = ensure_managed_serviceaccount(
            module, hub_client, managed_cluster_name, ttl_seconds)

        # wait service account secret
        if wait:
            wait_for_serviceaccount_secret(
                module, hub_client, managed_serviceaccount, timeout)

        # grab secret
        secret = get_hub_serviceaccount_secret(
            hub_client, managed_serviceaccount)
        if secret is None:
            msan = managed_serviceaccount.metadata.name
            mcn = managed_cluster_name
            module.fail_json(
                msg=f'failed to get secret: secret of managedserviceaccount {msan} of cluster {mcn} is not found')

        # get token
        token_bytes = base64.b64decode(secret.data.token)
        token = token_bytes.decode('ascii')
        ret = {
            'name': managed_serviceaccount.metadata.name,
            'managed_cluster': managed_cluster_name,
            'token': token,
        }
        module.exit_json(
            changed=True, **ret, msg=f'managed serviceaccount {ret.get("name","")} is ready.')
    elif state == 'absent':
        managed_serviceaccount_name = module.params['name']
        ret = {
            'name': managed_serviceaccount_name,
            'managed_cluster': managed_cluster_name,
            'token': None,
        }
        managed_serviceaccount = get_managed_serviceaccount(
            hub_client, managed_cluster_name, managed_serviceaccount_name)

        if managed_serviceaccount is None:
            module.exit_json(
                changed=False, **ret, msg=f'managed serviceaccount {managed_serviceaccount_name} is deleted.')

        if delete_managed_serviceaccount(hub_client, managed_serviceaccount):
            module.exit_json(
                changed=True, **ret, msg=f'managed serviceaccount {managed_serviceaccount_name} is deleted.')
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
        generate_name=dict(type='str'),
        ttl_seconds_after_creation=dict(type='int', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ("state", "absent", ["name"]),
        ],
        required_one_of=[["name", "generate_name"]],
        mutually_exclusive=[["name", "generate_name"]],
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
