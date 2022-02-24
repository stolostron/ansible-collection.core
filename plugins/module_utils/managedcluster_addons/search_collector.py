from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from .addon_base import addon_base
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
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

    def check_feature(self):
        mch = self.get_multi_cluster_hub()
        if not self.get_multi_cluster_hub_feature_enablement(mch):
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
        mch = self.get_multi_cluster_hub()
        changed = False
        if not self.get_multi_cluster_hub_feature_enablement(mch):
            # need to update mch
            self.update_multi_cluster_hub_feature(mch, True)
            changed = True
        # if self.wait:
            # waiting for clusterdeployment is not doable

            # cluster_management_addon_api = self.hub_client.resources.get(
            #     api_version='addon.open-cluster-management.io/v1alpha1',
            #     kind='ClusterManagementAddOn',
            # )
            # try:
            #     cluster_management_addon_api.get(name=self.addon_name)
            # except NotFoundError:
            #     if not self.wait_for_feature_enabled():
            #         self.module.fail_json(msg=f'timeout waiting for the feature {self.addon_name} to be enabled.')
        return changed

    def disable_feature(self):
        mch = self.get_multi_cluster_hub()
        changed = False
        if self.get_multi_cluster_hub_feature_enablement(mch):
            # need to update mch
            changed = True
            self.update_multi_cluster_hub_feature(mch, False)
        return changed

    def update_multi_cluster_hub_feature(self, mch, state=False):
        mch_api = self.hub_client.resources.get(
            api_version="operator.open-cluster-management.io/v1",
            kind="MultiClusterHub",
        )
        patch_body = {
            "apiVersion": "operator.open-cluster-management.io/v1",
            "kind": "MultiClusterHub",
            "metadata": {
                "name": mch.metadata.name,
                "namespace": mch.metadata.namespace,
            },
            "spec": {
                "componentConfig": {
                    "search": {
                        "disable": not state,
                    },
                },
            },
        }
        try:
            mch_api.patch(body=patch_body,
                          content_type="application/merge-patch+json")
        except DynamicApiError as e:
            self.module.fail_json(
                msg=f'failed to patch MultiClusterHub {mch.metadata.name} in {mch.metadata.namespace} namespace.', err=e)

    def get_multi_cluster_hub_feature_enablement(self, mch):
        mch_feature_path = ['spec', 'componentConfig', 'search', 'disable']
        curr = mch
        for p in mch_feature_path[:-1]:
            next = curr.get(p)
            if next is None:
                return True
            curr = next
        return curr.get(mch_feature_path[-1]) is False
