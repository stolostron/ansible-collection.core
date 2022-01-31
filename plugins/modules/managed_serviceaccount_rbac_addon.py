#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managed_serviceaccount_rbac_addon

short_description: cluster proxy addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use the managed-serviceaccount RBAC addon to setup a serviceaccount on a managedcluster with the specified RBAC permission,
    and return the serviceaccount token.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    managed_cluster:
        description: Name of the managed cluster.
        type: str
        required: True
    managed_serviceaccount:
        description: Managed serviceaccount information.
        type: dict
        required: True
    rbac_template:
        description: Path to the RBAC role/clusterrrole/rolebinding/clusterrolebinding file or directory.
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
'''

EXAMPLES = r'''
- name: "Configure RBAC"
  ocmplus.cm.managed_serviceaccount_rbac_addon:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    managed_serviceaccount: managed_serviceaccount
    rbac_template: /path/to/rbac_template
    wait: True
    timeout: 60
  register: token
'''

RETURN = r'''
token:
    description: The token of the ServiceAccount
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

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import generate_random_string

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
try:
    import os
except ImportError as e:
    IMP_ERR['os'] = {'error': traceback.format_exc(),
                     'exception': e}


MANIFEST_WORK_TEMPLATE = """
apiVersion: work.open-cluster-management.io/v1
kind: ManifestWork
metadata:
  name: {{ managed_service_account_name }}
  namespace: {{ cluster_name }}
  ownerReferences:
  - apiVersion: {{ owner_api_version }}
    kind: {{ owner_kind }}
    name: {{ owner_name }}
    uid: {{ owner_uid }}
    blockOwnerDeletion: true
    controller: true
spec:
  workload:
    manifests: []
"""


def ensure_managed_service_account_rbac(module: AnsibleModule, hub_client, managed_cluster_name, managed_serviceaccount, rbac_template):
    if 'jinja2' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('jinja2'),
                         exception=IMP_ERR['jinja2']['exception'])
    if 'yaml' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('yaml'),
                         exception=IMP_ERR['yaml']['exception'])
    if 'os' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('os'),
                         exception=IMP_ERR['os']['exception'])                         


    managed_service_account_name = managed_serviceaccount[
        'managed_serviceaccount']['service_account']['name']
    managed_service_account_namespace = managed_serviceaccount[
        'managed_serviceaccount']['service_account']['namespace']
    random_string = generate_random_string()

    new_manifest_work_raw = Template(MANIFEST_WORK_TEMPLATE).render(
        cluster_name=managed_cluster_name,
        managed_service_account_name=managed_service_account_name,
        owner_api_version=managed_serviceaccount[
            'managed_serviceaccount']['api_version'],
        owner_kind=managed_serviceaccount[
            'managed_serviceaccount']['kind'],
        owner_name=managed_serviceaccount[
            'managed_serviceaccount']['name'],
        owner_uid=managed_serviceaccount[
            'managed_serviceaccount']['uid'],
    )

    new_manifest_work = yaml.safe_load(new_manifest_work_raw)

    role_subject = {'kind': 'ServiceAccount',
                    'name': managed_service_account_name,
                    'namespace': managed_service_account_namespace}
    role_names = []
    filenames = []

    if not os.path.exists(rbac_template):
        module.fail_json(
            msg=f'error: RBAC template file or directory {rbac_template} does not exists!')
        return None
    elif os.path.isdir(rbac_template):
        names = next(os.walk(rbac_template), (None, None, []))[2]
        for name in names:
            filenames.append(f'{rbac_template}/{name}')
        if len(filenames) == 0:
            module.fail_json(
                msg=f'error: RBAC template directory {rbac_template} is empty!')
            return None
    else:
        filenames.append(rbac_template)

    try:
        for filename in filenames:
            with open(filename, 'r') as file:
                docs = yaml.safe_load_all(file)
                for doc in docs:
                    if doc['kind'] in ['Role', 'ClusterRole']:
                        role_names.append(doc['metadata']['name'])
                        doc['metadata']['name'] = f"{doc['metadata']['name']}-{random_string}"
                    elif doc['kind'] in ['RoleBinding', 'ClusterRoleBinding']:
                        doc['metadata']['name'] = f"{doc['metadata']['name']}-{random_string}"
                        if doc['roleRef']['name'] in role_names:
                            doc['roleRef']['name'] = f"{doc['roleRef']['name']}-{random_string}"
                        if 'subjects' in doc.keys():
                            doc['subjects'].append(role_subject)
                        else:
                            doc['subjects'] = []
                            doc['subjects'].append(role_subject)

                    new_manifest_work['spec']['workload']['manifests'].append(
                        doc)
    except Exception:
        module.fail_json(
            msg=f'error: invalid RBAC template file {filename}')

    manifest_work_api = hub_client.resources.get(
        api_version='work.open-cluster-management.io/v1',
        kind='ManifestWork',
    )

    manifest_work = manifest_work_api.create(new_manifest_work)

    return manifest_work


def wait_for_manifestwork_available(module: AnsibleModule, hub_client, manifestwork, timeout=60) -> bool:
    manifest_work_api = hub_client.resources.get(
        api_version='work.open-cluster-management.io/v1',
        kind='ManifestWork',
    )

    for event in manifest_work_api.watch(namespace=manifestwork.metadata.namespace, timeout=timeout):
        if event['type'] in ['ADDED', 'MODIFIED'] and event['object'].metadata.name == manifestwork.metadata.name:
            if 'status' in event['object'].keys():
                conditions = event['object']['status'].get('conditions', [])
                for condition in conditions:
                    if condition['type'] == 'Available' and condition['status'] == 'True':
                        return True

    return False


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    managed_cluster_name = module.params['managed_cluster']
    managed_serviceaccount = module.params['managed_serviceaccount']
    rbac_template = module.params['rbac_template']
    wait = module.params['wait']
    timeout = module.params['timeout']
    if timeout is None or timeout <= 0:
        timeout = 60

    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )

    managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
    if managed_cluster is None:
        module.fail_json(
            msg=f'failed to get managedcluster {managed_cluster_name}')

    manifest_work = ensure_managed_service_account_rbac(
        module, hub_client, managed_cluster_name, managed_serviceaccount, rbac_template)

    if wait:
        wait_for_manifestwork_available(
            module, hub_client, manifest_work, timeout)

    module.exit_json(
        token=managed_serviceaccount['managed_serviceaccount']['service_account']['token'])


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        managed_serviceaccount=dict(type='dict', required=True),
        rbac_template=dict(type='str', required=True),
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
