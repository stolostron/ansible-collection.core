from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from .addon_base import addon_base
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.installer_utils import get_multi_cluster_hub, get_component_status, set_component_status
IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import DynamicApiError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}

# subclass


class search_collector(addon_base):
    def __init__(self, module: AnsibleModule, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
        super().__init__(module, hub_client, managed_cluster_name, addon_name, wait, timeout)
        if 'k8s' in IMP_ERR:
            module.fail_json(msg=missing_required_lib('kubernetes'),
                             exception=IMP_ERR['k8s']['exception'])
        self.component_name = 'search'

    def check_feature(self):
        mch = self.get_multi_cluster_hub()
        if not get_component_status(mch, self.module, self.component_name):
            self.module.fail_json(
                msg=f'failed to check feature: {self.addon_name} is not enabled')

    def enable_addon(self):
        return self.enable_klusterlet_addon(
            self.module,
            self.hub_client,
            self.managed_cluster_name,
            self.addon_name,
            self.wait,
            self.timeout
        )

    def disable_addon(self):
        return self.disable_klusterlet_addon(
            self.module,
            self.hub_client,
            self.managed_cluster_name,
            self.addon_name,
            self.wait,
            self.timeout
        )

    def enable_feature(self):
        mch = get_multi_cluster_hub(self.hub_client, self.module).to_dict()
        changed = False
        if not get_component_status(mch, self.module, self.component_name):
            # need to update mch
            self.update_multi_cluster_hub_feature(mch, True)
            changed = True
        return changed

    def disable_feature(self):
        mch = get_multi_cluster_hub(self.hub_client, self.module).to_dict()
        changed = False
        if get_component_status(mch, self.module, self.component_name):
            # need to update mch
            changed = True
            self.update_multi_cluster_hub_feature(mch, False)
        return changed

    def update_multi_cluster_hub_feature(self, mch, state=False):
        mch_api = self.hub_client.resources.get(
            api_version="operator.open-cluster-management.io/v1",
            kind="MultiClusterHub",
        )
        set_component_status(mch, self.module, self.component_name, state)
        try:
            mch_api.patch(
                name=mch.get('metadata', {}).get('name'),
                namespace=mch.get('metadata', {}).get('namespace'),
                body=mch,
                content_type="application/merge-patch+json")
        except DynamicApiError as e:
            self.module.fail_json(
                msg=f'failed to patch MultiClusterHub {mch.metadata.name} in {mch.metadata.namespace} namespace.', exception=e)
