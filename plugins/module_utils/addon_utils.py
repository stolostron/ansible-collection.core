from __future__ import (absolute_import, division, print_function)
from logging import exception

__metaclass__ = type

import time
import string
import random
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError
    from kubernetes.client.exceptions import ApiException
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}

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


ADDON_TEMPLATE = """
apiVersion: addon.open-cluster-management.io/v1alpha1
kind: ManagedClusterAddOn
metadata:
  name: {{ addon_name }}
  namespace: {{ managed_cluster_name }}
spec:
  installNamespace: {{ addon_install_namespace }}
"""


def get_managed_cluster_addon(hub_client, cluster_name: str, addon_name: str):
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )
    try:
        managed_cluster_addon = managed_cluster_addon_api.get(
            name=addon_name,
            namespace=cluster_name,
        )
        return managed_cluster_addon
    except NotFoundError:
        return None


def check_managed_cluster_addon_available(managed_cluster_addon) -> bool:
    if managed_cluster_addon is None:
        return False
    if "status" in managed_cluster_addon.keys():
        conditions = managed_cluster_addon.status.get("conditions", [])
        for condition in conditions:
            if condition.type == 'Available':
                return condition.status == 'True'
    return False


def check_addon_available(hub_client, cluster_name: str, addon_name: str):
    addon = get_managed_cluster_addon(hub_client, cluster_name, addon_name)
    return check_managed_cluster_addon_available(addon)


def wait_for_addon_available(module: AnsibleModule, hub_client, managed_cluster_name, addon_name, timeout=60) -> bool:
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )

    start_time = time.time()
    while time.time() - start_time < timeout:
        for event in managed_cluster_addon_api.watch(namespace=managed_cluster_name, timeout=timeout):
            if event["type"] in ["ADDED", "MODIFIED"] and event["object"].metadata.name == addon_name:
                if "status" in event["object"].keys():
                    conditions = event["object"]["status"].get(
                        "conditions", [])
                    for condition in conditions:
                        if condition["type"] == "Available" and condition["status"] == "True":
                            return True

    return False


def wait_for_addon_not_available(module: AnsibleModule, hub_client, managed_cluster_name, addon_name, timeout=60) -> bool:
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )

    for event in managed_cluster_addon_api.watch(namespace=managed_cluster_name, timeout=timeout):
        if event["type"] == "DELETED" and event["object"].metadata.name == addon_name:
            return True

    return False


def ensure_managed_cluster_addon_enabled(
    module: AnsibleModule,
    hub_client,
    addon_name: str,
    managed_cluster_name: str,
    addon_install_namespace: str = "open-cluster-management-agent-addon"
):
    if 'k8s' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )
    addon = None
    try:
        addon = managed_cluster_addon_api.get(
            name=addon_name,
            namespace=managed_cluster_name,
        )
        return module.exit_json(
            changed=False, result=f'addon: {addon_name} is already enabled in {managed_cluster_name}')
    except NotFoundError:
        if 'jinja2' in IMP_ERR:
            module.fail_json(msg=missing_required_lib(
                'jinja2'), exception=IMP_ERR['jinja2']['exception'])
        if 'yaml' in IMP_ERR:
            module.fail_json(msg=missing_required_lib('yaml'),
                             exception=IMP_ERR['yaml']['exception'])
        new_addon_yaml = Template(ADDON_TEMPLATE).render(
            addon_name=addon_name,
            managed_cluster_name=managed_cluster_name,
            addon_install_namespace=addon_install_namespace,
        )
        new_addon = yaml.safe_load(new_addon_yaml)
        try:
            addon = managed_cluster_addon_api.create(new_addon)
        except DynamicApiError as e:
            module.fail_json(
                msg=f'failed to create managedclusteraddon {addon_name}', exception=e)

    return addon


def generate_random_string(size: int = 16):
    return ''.join(random.choice(string.ascii_lowercase + string.digits) for s in range(size))


def delete_managed_cluster_addon(hub_client, managed_cluster_addon):
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )

    status = managed_cluster_addon_api.delete(
        namespace=managed_cluster_addon.metadata.namespace,
        name=managed_cluster_addon.metadata.name,
    )

    return (status.status == 'Success')


def ensure_klusterlet_addon(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60) -> dict:
    addon_controller_map = {
        "policy-controller": "policyController",
        "cert-policy-controller": "certPolicyController",
        "iam-policy-controller": "iamPolicyController",
        "application-manager": "applicationManager",
        "search-collector": "searchCollector"

    }
    enabled_disabled = 'enabled' if enabled else 'disabled'
    # get all instance of KlusterletAddonConfig
    kac_api = hub_client.resources.get(
        api_version="agent.open-cluster-management.io/v1",
        kind="KlusterletAddonConfig",
    )

    kac_list = kac_api.get(namespace=managed_cluster_name)
    if len(kac_list.get('items', [])) != 1:
        return module.fail_json(
            msg=f'KlusterletAddonConfig in namespace: {managed_cluster_name} not found')

    kac = kac_list.items[0]
    if getattr(kac.spec, addon_controller_map[addon_name]).enabled == enabled:
        return module.exit_json(
            changed=False, result=f'addon: {addon_name} is already {enabled_disabled} in {managed_cluster_name}')

    getattr(kac.spec, addon_controller_map[addon_name]).enabled = enabled
    try:
        kac = kac_api.patch(
            name=kac.metadata.name,
            namespace=kac.metadata.namespace,
            body=kac_list.to_dict()['items'][0],
            content_type="application/merge-patch+json",
        )
    except ApiException:
        module.fail_json(
            msg=f'failed to enable klusterletaddonconfig addon: {addon_name}')

    if enabled:
        if wait:
            wait_for_addon_available(
                module, hub_client, managed_cluster_name, addon_name, timeout)
        if check_addon_available(hub_client, managed_cluster_name, addon_name):
            return module.exit_json(
                changed=True, result=f'addon: {addon_name} enabled in {managed_cluster_name} successfully')
        else:
            return module.fail_json(
                msg=f'failed to enable addon: {addon_name}')
    else:
        if wait:
            wait_for_addon_not_available(
                module, hub_client, managed_cluster_name, addon_name, timeout)
        if not check_addon_available(hub_client, managed_cluster_name, addon_name):
            return module.exit_json(
                changed=True, result=f'addon: {addon_name} disabled in {managed_cluster_name} successfully')
        else:
            return module.fail_json(
                msg=f'failed to disable addon: {addon_name}')


def check_multi_cluster_hub_feature(module: AnsibleModule, hub_client, addon_name) -> dict:
    addon_feature_map = {
        "cluster-proxy": "enableClusterProxyAddon",
        "managed-serviceaccount": "managedServiceAccount"
    }
    # get all instance of mch
    mch_api = hub_client.resources.get(
        api_version="operator.open-cluster-management.io/v1",
        kind="MultiClusterHub",
    )

    mch_list = mch_api.get()
    if len(mch_list.get('items', [])) != 1:
        return module.fail_json(
            msg='MultiClusterHub not found')

    mch = mch_list.items[0]
    if not getattr(mch.spec, addon_feature_map[addon_name]):
        return module.fail_json(
            msg=f'failed to check feature: {addon_feature_map[addon_name]} of MultiClusterHub is not enabled')


def check_cluster_management_addon_feature(module: AnsibleModule, hub_client, addon_name):
    cluster_management_addon_api = hub_client.resources.get(
        api_version='addon.open-cluster-management.io/v1alpha1',
        kind='ClusterManagementAddOn',
    )

    try:
        return cluster_management_addon_api.get(name=addon_name)
    except NotFoundError:
        return module.fail_json(
            msg=f'failed to check feature: {addon_name} of ClusterManagementAddOn is not enabled')


def ensure_managed_cluster_addon(module: AnsibleModule, enabled, hub_client, managed_cluster_name, addon_name, wait=False, timeout=60):
    if enabled:
        ensure_managed_cluster_addon_enabled(
            module, hub_client, addon_name, managed_cluster_name)

        if wait:
            wait_for_addon_available(
                module, hub_client, managed_cluster_name, addon_name, timeout)

        if check_addon_available(hub_client, managed_cluster_name, addon_name):
            return module.exit_json(
                changed=True, result=f'addon: {addon_name} enabled in {managed_cluster_name} successfully')
        else:
            return module.fail_json(
                msg=f'failed to enable addon: {addon_name}')
    else:
        managed_cluster_addon = get_managed_cluster_addon(
            hub_client, managed_cluster_name, addon_name)
        if managed_cluster_addon is None:
            return module.exit_json(
                changed=False, result=f'addon: {addon_name} in {managed_cluster_name} is not found or already disabled')
        if delete_managed_cluster_addon(hub_client, managed_cluster_addon):
            return module.exit_json(
                changed=True, result=f'addon: {addon_name} disabled in {managed_cluster_name} successfully')
        else:
            return module.fail_json(
                msg=f'failed to disable addon: {addon_name}')
