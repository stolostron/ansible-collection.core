#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: addon

short_description: addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Use addon to enable/disable an addon on a managedcluster.

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
        choices: [ cluster-proxy, managed-serviceaccount, policy-controller, cert-policy-controller,
                   iam-policy-controller, application-manager, search-collector  ]
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
  ocmplus.cm.addon:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    addon_name: cluster-proxy
    wait: True
    timeout: 120

- name: "Disabled cluster-proxy addon"
  ocmplus.cm.addon:
    state: absent
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
    addon_name: cluster-proxy
    wait: True
    timeout: 60
'''

RETURN = r'''
result:
    description: message describing the addon enabled/disabled successfully done.
    returned: success
    type: str
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    check_multi_cluster_hub_feature,
    check_cluster_management_addon_feature,
    ensure_klusterlet_addon,
    ensure_managed_cluster_addon,
)

IMP_ERR = {}
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def cluster_proxy(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_multi_cluster_hub_feature(module, hub_client, addon_name)

    return ensure_managed_cluster_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def managed_serviceaccount(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        # check_multi_cluster_hub_feature(module, hub_client, addon_name)
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_managed_cluster_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def policy_controller(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_klusterlet_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def cert_policy_controller(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_klusterlet_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def iam_policy_controller(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_klusterlet_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def application_manager(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_klusterlet_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


def search_collector(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        check_cluster_management_addon_feature(module, hub_client, addon_name)

    return ensure_klusterlet_addon(module, enabled, hub_client, managed_cluster_name, addon_name, wait, timeout)


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
    globals()[new_addon_name](module, enabled, hub_client,
                              managed_cluster_name, addon_name, wait, timeout)


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        addon_name=dict(
            type='str',
            choices=[
                "cluster-proxy",
                "managed-serviceaccount",
                "policy-controller",
                "cert-policy-controller",
                "iam-policy-controller",
                "application-manager",
                "search-collector"
            ],
            required=True
        ),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60),
        state=dict(
            type="str",
            default="present",
            choices=["present", "absent"],
            require=True
        ),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
