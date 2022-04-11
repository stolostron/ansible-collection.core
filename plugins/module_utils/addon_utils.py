from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import traceback

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


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
