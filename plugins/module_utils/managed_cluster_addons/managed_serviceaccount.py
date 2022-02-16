from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    check_multi_cluster_hub_feature,
    check_cluster_management_addon_feature,
    ensure_managed_cluster_addon,
)


class managed_serviceaccount:
    def __init__(self, module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
        self.module = module
        self.enabled = enabled
        self.hub_client = hub_client
        self.managed_cluster_name = managed_cluster_name
        self.addon_name = addon_name
        self.wait = wait
        self.timeout = timeout

    def run(self):
        if self.enabled:
            # check_multi_cluster_hub_feature(
            #  self.module,
            #  self.hub_client,
            #  self.addon_name
            # )
            check_cluster_management_addon_feature(
                self.module,
                self.hub_client,
                self.addon_name
            )

        return ensure_managed_cluster_addon(
            self.module,
            self.enabled,
            self.hub_client,
            self.managed_cluster_name,
            self.addon_name,
            self.wait,
            self.timeout
        )
