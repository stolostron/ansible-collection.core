#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managedcluster_addon

short_description: managed cluster addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use managedcluster_addon to enable/disable an addon on a managedcluster.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    wait:
        description: Whether to wait for addon to show up.
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the addon to show up.
        type: int
        default: 60
        required: False
    managed_cluster:
        description: Name of managed cluster to enabled addon.
        type: str
        required: True
    addon_name:
        description: Name of the addon to enable/disable on a managed cluster.
        type: str
        choices: [  application-manager,
                    cert-policy-controller,
                    cluster-proxy,
                    iam-policy-controller,
                    managed-serviceaccount,
                    policy-controller,
                    search-collector
                 ]
        required: True
    state:
        description:
        - Determines if addon should be enabled, or disabled. When set to C(present),
          an addon will be enabled. If set to C(absent), an existing addon will be disabled.
        type: str
        default: present
        choices: [ absent, present ]
        required: False
'''

EXAMPLES = r'''
- name: "Enabled cluster-proxy addon"
  stolostron.core.managedcluster_addon:
    state: present
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    addon_name: cluster-proxy
    wait: True
    timeout: 120

- name: "Disabled cluster-proxy addon"
  stolostron.core.managedcluster_addon:
    state: absent
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    addon_name: cluster-proxy
    wait: True
    timeout: 60
'''

RETURN = r'''
msg:
    description: message describing the addon enabled/disabled successfully done.
    returned: success
    type: str
exception:
    description: exception catched during the process.
    returned: when exception is catched
    type: complex
    contains: {}
'''

import os
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.application_manager import application_manager
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.cert_policy_controller import cert_policy_controller
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.cluster_proxy import cluster_proxy
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.iam_policy_controller import iam_policy_controller
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.managed_serviceaccount import managed_serviceaccount
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.policy_controller import policy_controller
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.search_collector import search_collector
from pkgutil import iter_modules
from pathlib import Path

IMP_ERR = {}
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    addon_name = module.params['addon_name']
    managed_cluster_name = module.params['managed_cluster']
    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )
    wait = module.params['wait']
    timeout = module.params['timeout']
    if timeout is None or timeout <= 0:
        timeout = 60

    state = module.params['state']
    if state == 'present':
        managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
        if managed_cluster is None:
            module.fail_json(
                msg=f'failed to get managedcluster {managed_cluster_name}')

    enabled = True if state == 'present' else False
    new_addon_name = addon_name.replace('-', '_')
    new_addon = globals()[new_addon_name](
        module, hub_client, managed_cluster_name, addon_name, wait, timeout)
    if enabled:
        new_addon.check_feature()
        new_addon.enable_addon()
    else:
        new_addon.disable_addon()


def main():
    current_path = os.path.dirname(__file__)
    path = current_path[:current_path.rfind('/')]
    addons_path = f'{path}/module_utils/managedcluster_addons'
    package_dir = Path(addons_path).resolve()
    addon_choices = []
    for (loader, module_name, ispkg) in iter_modules([package_dir]):
        if module_name != 'addon_base':
            addon_choices.append(module_name.replace('_', '-'))

    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        addon_name=dict(
            type='str',
            choices=addon_choices,
            required=True
        ),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60),
        state=dict(
            type="str",
            default="present",
            choices=["present", "absent"],
            required=False
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
