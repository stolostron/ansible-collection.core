#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''

module: cluster_management_addon

short_description: cluster management addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use cluster_management_addon to enable/disable a feature on the hub.
  Users can only install an addon on managed clusters if the feature of that addon is enabled.
  This plugin will need access to the Multicloudhub CR, and it enables/disables available features by updating the corresponding fields in the CR.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    wait:
        description: Whether to wait for an addon feature to show up. This configuration will be ignored when the state is 'absent'.
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the addon to show up.
        type: int
        default: 60
        required: False
    addon_name:
        description: Name of the feature to enable/disable.
        type: str
        choices: [
                    cluster-proxy,
                    managed-serviceaccount,
                    search-collector,
                 ]
        required: True
    state:
        description:
        - Determines if feature should be enabled, or disabled. When set to C(present),
          a feature will be enabled. If set to C(absent), an existing feature will be disabled.
        type: str
        default: present
        choices: [ absent, present ]
        required: False
'''

EXAMPLES = r'''
- name: "Enabled cluster-proxy addon"
  stolostron.core.cluster_management_addon:
    state: present
    hub_kubeconfig: /path/to/hub/kubeconfig
    addon_name: cluster-proxy

- name: "Disabled cluster-proxy addon"
  stolostron.core.cluster_management_addon:
    state: absent
    hub_kubeconfig: /path/to/hub/kubeconfig
    addon_name: cluster-proxy
'''

RETURN = r'''
msg:
    description: human readable message describing the addon is enabled/disabled.
    returned: always
    type: str
exception:
    description: exception catched during the process.
    returned: when exception is catched
    type: complex
    contains: {}
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.cluster_proxy import cluster_proxy
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.managed_serviceaccount import managed_serviceaccount
from ansible_collections.stolostron.core.plugins.module_utils.managedcluster_addons.search_collector import search_collector

IMP_ERR = {}
try:
    import kubernetes
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    addon_name = module.params['addon_name']
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
    enabled = True if state == 'present' else False
    new_addon_name = addon_name.replace('-', '_')
    new_addon = globals()[new_addon_name](module, hub_client,
                                          '', addon_name, wait, timeout)
    changed = False
    if enabled:
        changed = new_addon.enable_feature()
    else:
        changed = new_addon.disable_feature()

    module.exit_json(
        changed=changed, msg=f'Addon feature {addon_name} is {"enabled" if enabled else "disabled"}.')


def main():
    addon_choices = ['cluster-proxy',
                     'managed-serviceaccount', 'search-collector']

    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
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
