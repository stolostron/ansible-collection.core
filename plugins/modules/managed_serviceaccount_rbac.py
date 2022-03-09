#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managed_serviceaccount_rbac

short_description: managed-serviceaccount RBAC

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use the managed-serviceaccount RBAC to setup a serviceaccount on a managedcluster with the specified RBAC permission.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    managed_cluster:
        description: Name of the managed cluster.
        type: str
        required: True
    managed_serviceaccount_name:
        description: Name of managed-serviceaccount.
        type: str
        required: True
    rbac_template:
        description:
        - Path to the file or directory that contains the role/clusterrrole/rolebinding/clusterrolebinding configuration.
        - The path specified should either be the absolute or relative to the location of the playbook.
        - In order to avoid potential resource name collision, the name specified in the RBAC files
          will be appended with the last 12 digit of UID of the target managed-serviceaccount.
        type: path
        required: True
    wait:
        description: Whether to wait for the resources to show up.
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the resources to show up.
        type: int
        default: 60
        required: False
'''

EXAMPLES = r'''
- name: "Configure RBAC"
  ocmplus.cm.managed_serviceaccount_rbac:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    managed_serviceaccount_name: managed-serviceaccount-name
    rbac_template: /path/to/rbac_template
    wait: True
    timeout: 60
'''

RETURN = r'''
result:
    description:
    - message describing the RBAC configuration successfully done.
    returned: success
    type: str
'''

import os
import string
import random
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import get_managed_cluster_addon

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


MANIFEST_WORK_TEMPLATE = """
apiVersion: work.open-cluster-management.io/v1
kind: ManifestWork
metadata:
  name: {{ owner_name }}
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


def ensure_managed_service_account_rbac(
        module: AnsibleModule,
        hub_client,
        managed_cluster_name,
        managed_serviceaccount_name,
        rbac_template
):
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

    managed_service_account = managed_service_account_api.get(
        name=managed_serviceaccount_name,
        namespace=managed_cluster_name,
    )

    if managed_service_account is None:
        module.fail_json(
            msg=f"failed to get managed serviceaccount {managed_serviceaccount_name}")

    managed_service_account_addon = get_managed_cluster_addon(
        hub_client, managed_cluster_name, 'managed-serviceaccount')

    if managed_service_account_addon is None:
        module.fail_json(
            msg="failed to get managed serviceaccount addon managed-serviceaccount")

    random_string = managed_service_account.metadata.uid.split('-')[-1]

    new_manifest_work_raw = Template(MANIFEST_WORK_TEMPLATE).render(
        cluster_name=managed_cluster_name,
        owner_name=managed_service_account.metadata.name,
        owner_api_version=managed_service_account.apiVersion,
        owner_kind=managed_service_account.kind,
        owner_uid=managed_service_account.metadata.uid,
    )

    new_manifest_work = yaml.safe_load(new_manifest_work_raw)

    role_subject = {'kind': 'ServiceAccount',
                    'name': managed_service_account.metadata.name,
                    'namespace': managed_service_account_addon.spec.installNamespace}

    # get the filename for all the rbac files
    filenames = []
    if not os.path.exists(rbac_template):
        module.fail_json(
            msg=f"error: RBAC template file or directory {rbac_template} does not exists!")
        return None
    if os.path.isdir(rbac_template):
        names = next(os.walk(rbac_template), (None, None, []))[2]
        for name in names:
            filenames.append(f"{rbac_template}/{name}")
        if len(filenames) == 0:
            module.fail_json(
                msg=f"error: RBAC template directory {rbac_template} is empty!")
            return None
    else:
        filenames.append(rbac_template)

    # gather all the yaml from files
    yaml_resources = []
    try:
        for filename in filenames:
            with open(filename, 'r') as file:
                for resource in yaml.safe_load_all(file):
                    yaml_resources.append(resource)
    except Exception as err:
        module.fail_json(
            msg=f"error: fail to read RBAC template file {filename} {err}")

    # split up the yaml resources base on their type
    # this will also filter out non RBAC resources
    rbac_kinds = ['Role', 'ClusterRole', 'RoleBinding', 'ClusterRoleBinding']
    rbac_resources = dict()
    for kind in rbac_kinds:
        rbac_resources[kind] = []

    for resource in yaml_resources:
        if resource['kind'] in rbac_kinds:
            rbac_resources[resource['kind']].append(resource)

    # if the clusterrolebinding/rolebinding contains subject
    # we ignore them because we only allow binding to the managed-serviceaccount
    for rolebinding in rbac_resources['ClusterRoleBinding'] + rbac_resources['RoleBinding']:
        # make rolebinding name unique
        rolebinding['metadata']['name'] = f"{rolebinding['metadata']['name']}-{random_string}"
        rolebinding['subjects'] = [role_subject]

    for clusterrolebinding in rbac_resources['ClusterRoleBinding']:
        for clusterrole in rbac_resources['ClusterRole']:
            if clusterrole['metadata']['name'] == clusterrolebinding['roleRef']['name']:
                clusterrolebinding['roleRef']['name'] = f"{clusterrolebinding['roleRef']['name']}-{random_string}"

    for rolebinding in rbac_resources['RoleBinding']:
        if rolebinding['roleRef']['kind'] == 'Role':
            for role in rbac_resources['Role']:
                if (
                    role['metadata']['name'] == rolebinding['roleRef']['name'] and
                    role['metadata']['namespace'] == rolebinding['metadata']['namespace']
                ):
                    rolebinding['roleRef']['name'] = f"{rolebinding['roleRef']['name']}-{random_string}"
        elif rolebinding['roleRef']['kind'] == 'ClusterRole':
            for clusterrole in rbac_resources['ClusterRole']:
                if clusterrole['metadata']['name'] == rolebinding['roleRef']['name']:
                    rolebinding['roleRef']['name'] = f"{rolebinding['roleRef']['name']}-{random_string}"

    for role in rbac_resources['ClusterRole'] + rbac_resources['Role']:
        # make rolebinding name unique
        role['metadata']['name'] = f"{role['metadata']['name']}-{random_string}"

    for resources in rbac_resources.values():
        for resource in resources:
            new_manifest_work['spec']['workload']['manifests'].append(resource)

    manifest_work_api = hub_client.resources.get(
        api_version='work.open-cluster-management.io/v1',
        kind='ManifestWork',
    )

    manifest_work = None
    try:
        manifest_work = manifest_work_api.get(
            namespace=managed_cluster_name,
            name=managed_serviceaccount_name,
        )
    except NotFoundError:
        manifest_work = None

    if manifest_work is None:
        manifest_work = manifest_work_api.create(new_manifest_work)
    else:
        manifest_work = manifest_work_api.patch(
            namespace=managed_cluster_name,
            name=managed_serviceaccount_name,
            body=new_manifest_work,
            content_type="application/merge-patch+json",
        )

    #TODO detect manifestwork failure and report failure
    
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
    managed_serviceaccount_name = module.params['managed_serviceaccount_name']
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
            msg=f"failed to get managedcluster {managed_cluster_name}")

    manifest_work = ensure_managed_service_account_rbac(
        module, hub_client, managed_cluster_name, managed_serviceaccount_name, rbac_template)

    if wait:
        wait_for_manifestwork_available(
            module, hub_client, manifest_work, timeout)

    module.exit_json(
        result=f"RBAC configuration successfully done for managed cluster {managed_cluster_name}")


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        managed_serviceaccount_name=dict(type='str', required=True),
        rbac_template=dict(type='path', required=True),
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
