from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError
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


def get_managed_cluster_addon(hub_client, addon_name: str, cluster_name: str):
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )
    managed_cluster_addon = managed_cluster_addon_api.get(
        name=addon_name,
        namespace=cluster_name,
    )
    return managed_cluster_addon


def check_managed_cluster_addon_available(managed_cluster_addon) -> bool:
    if managed_cluster_addon is None:
        return False
    if "status" in managed_cluster_addon.keys():
        conditions = managed_cluster_addon.status.get("conditions", [])
        for condition in conditions:
            if condition.type == 'Available':
                return condition.status == 'True'
    return False


def check_addon_available(hub_client, addon_name: str, cluster_name: str):
    addon = get_managed_cluster_addon(hub_client, addon_name, cluster_name)
    return check_managed_cluster_addon_available(addon)


def wait_for_addon_available(module: AnsibleModule, hub_client, addon, timeout=60) -> bool:
    managed_cluster_addon_api = hub_client.resources.get(
        api_version="addon.open-cluster-management.io/v1alpha1",
        kind="ManagedClusterAddOn",
    )

    for event in managed_cluster_addon_api.watch(namespace=addon.metadata.namespace, timeout=timeout):
        if event["type"] in ["ADDED", "MODIFIED"] and event["object"].metadata.name == addon.metadata.name:
            if "status" in event["object"].keys():
                conditions = event["object"]["status"].get("conditions", [])
                for condition in conditions:
                    if condition["type"] == "Available" and condition["status"] == "True":
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
