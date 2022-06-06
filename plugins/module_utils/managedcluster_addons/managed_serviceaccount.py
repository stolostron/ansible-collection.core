from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from .addon_base import addon_base
import traceback
from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.installer_utils import (
    get_multi_cluster_hub,
    get_multi_cluster_engine,
    get_component_status,
    set_component_status
)

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError
    from kubernetes.client.exceptions import ApiException
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


# subclass
class managed_serviceaccount(addon_base):
    def __init__(self, module: AnsibleModule, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
        super().__init__(module, hub_client, managed_cluster_name, addon_name, wait, timeout)
        if 'k8s' in IMP_ERR:
            module.fail_json(msg=missing_required_lib('kubernetes'),
                             exception=IMP_ERR['k8s']['exception'])
        self.component_name = 'managedserviceaccount-preview'

    def check_feature(self):
        self.check_cluster_management_addon_feature(
            self.module,
            self.hub_client,
            self.addon_name
        )

    def enable_addon(self):
        return self.enable_managed_cluster_addon(
            self.module,
            self.hub_client,
            self.managed_cluster_name,
            self.addon_name,
            self.wait,
            self.timeout
        )

    def disable_addon(self):
        return self.disable_managed_cluster_addon(
            self.module,
            self.hub_client,
            self.managed_cluster_name,
            self.addon_name,
            self.wait,
            self.timeout
        )

    def enable_feature(self):
        changed = False
        mce = get_multi_cluster_engine(
            self.hub_client, self.module).to_dict()
        if not get_component_status(mce, self.module, self.component_name):
            # need to update mch
            self.update_multi_cluster_engine_feature(mce, True)
            changed = True
        mch = get_multi_cluster_hub(
            hub_client=self.hub_client, module=self.module, ignore_not_found=True)
        if mch is not None:
            mch = mch.to_dict()
            if not get_component_status(mch, self.module, self.component_name):
                # need to update mch
                self.update_multi_cluster_hub_feature(mch, True)
                changed = True

        if self.wait:
            # wait clusterdeployment to be created
            cluster_management_addon_api = self.hub_client.resources.get(
                api_version='addon.open-cluster-management.io/v1alpha1',
                kind='ClusterManagementAddOn',
            )
            try:
                cluster_management_addon_api.get(name=self.addon_name)
            except NotFoundError as e:
                if not self.wait_for_feature_enabled():
                    self.module.fail_json(
                        msg=f'timeout waiting for the feature {self.addon_name} to be enabled.', exception=e)

        return changed

    def disable_feature(self):
        changed = False
        mce = get_multi_cluster_engine(
            self.hub_client, self.module).to_dict()
        if get_component_status(mce, self.module, self.component_name):
            changed = True
            self.update_multi_cluster_engine_feature(mce, False)

        mch = get_multi_cluster_hub(
            hub_client=self.hub_client, module=self.module, ignore_not_found=True)
        if mch is not None:
            mch = mch.to_dict()
            if get_component_status(mch, self.module, self.component_name):
                # need to update mch
                changed = True
                self.update_multi_cluster_hub_feature(mch, False)

        return changed

    def update_multi_cluster_engine_feature(self, mce, state=False):
        mce_api = self.hub_client.resources.get(
            api_version="multicluster.openshift.io/v1",
            kind="MultiClusterEngine",
        )
        set_component_status(mce, self.module, self.component_name, state)
        try:
            mce_api.patch(
                name=mce.get('metadata', {}).get('name'),
                namespace=mce.get('metadata', {}).get('namespace'),
                body=mce,
                content_type="application/merge-patch+json")
        except DynamicApiError as e:
            self.module.fail_json(
                msg=f'failed to patch MultiClusterHub {mce.metadata.name}.', exception=e)

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

    # get_feature_enablement gets enablement of managedserviceaccount from a MultiClusterHub CR or a MultiClusterEngine CR
    def get_feature_enablement(self, mch):
        mch_feature_path = ['spec', 'componentConfig',
                            'managedServiceAccount', 'enable']
        curr = mch
        for p in mch_feature_path[:-1]:
            next = curr.get(p)
            if next is None:
                return False
            curr = next
        return curr.get(mch_feature_path[-1]) is True
