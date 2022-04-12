from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import traceback

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError, ResourceNotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def get_multi_cluster_hub(hub_client, module, ignore_not_found=False):
    """
    get_multi_cluster_hub lists mch of the cluster, and returns the first one.
    If ignore_not_found is set, will simply return None without sending any errors.
    """

    # get all instance of mch
    try:
        mch_api = hub_client.resources.get(
            api_version="operator.open-cluster-management.io/v1",
            kind="MultiClusterHub",
        )
        mch_list = mch_api.get()
    except (ResourceNotFoundError, NotFoundError) as e:
        if not ignore_not_found:
            module.fail_json(
                msg=f'failed to list MultiClusterHub: {e}', exception=e)
        return None

    if not ignore_not_found and len(mch_list.get('items', [])) < 1:
        module.fail_json(
            msg='failed to get MultiClusterHub.')

    if len(mch_list.get('items', [])) < 1:
        return None

    first_mch = mch_list.items[0]
    mch = None
    # get mch directly for return
    try:
        mch = mch_api.get(name=first_mch.metadata.name,
                          namespace=first_mch.metadata.namespace)
    except DynamicApiError as e:
        module.fail_json(
            msg=f'failed to get MultiClusterHub {first_mch.metadata.name} in {first_mch.metadata.namespace} namespace: {e}', exception=e)

    return mch


def get_multi_cluster_engine(hub_client, module):
    """
    get_multi_cluster_engine lists mce of the cluster, and returns the first one.
    """
    # get all instance of mce
    try:
        mce_api = hub_client.resources.get(
            api_version="multicluster.openshift.io/v1",
            kind="MultiClusterEngine",
        )
        mce_list = mce_api.get()
        if len(mce_list.get('items', [])) < 1:
            if module is not None:
                module.fail_json(
                    'failed to get MultiClusterEngine.')
            return None
    except DynamicApiError as e:
        if module is not None:
            module.fail_json(
                f'failed to get MultiClusterEngine: {e}.', exception=e)
        return None

    first_mce = mce_list.items[0]
    mce = None
    # get mce directly for return
    try:
        mce = mce_api.get(name=first_mce.metadata.name,
                          namespace=first_mce.metadata.namespace)
    except DynamicApiError as e:
        module.fail_json(
            msg=f'failed to get MultiClusterEngine {first_mce.metadata.name}: {e}', exception=e)

    return mce


def get_component_status(obj, module, component_name: str):
    """
    get_component_status returns a boolean to indicate if a certain component is enabled or disabled.
    obj can be either a dict of a MCH CR, or a dict of a MCE CR.
    If the component_name is not existed in the spec.components list, will return False.
    """
    if obj is None:
        return False
    obj_feature_path = ['spec', 'overrides', 'components']
    curr = obj
    for p in obj_feature_path:
        next = curr.get(p)
        if next is None:
            return False
        curr = next
    components = curr
    try:
        for component in components:
            if component.get('name', '') != component_name:
                continue
            return component.get('enabled', False)
    except (TypeError, AttributeError) as e:
        module.fail_json(
            msg=f'failed to get enablement status of component {component_name}: {e}', exception=e)

    return False


def set_component_status(obj, module, component_name: str, enabled: bool):
    """
    set_component_status sets the given obj with the given enabled status in place.
    obj can be either a dict of a MCH CR, or a dict of a MCE CR.
    If the obj is empty or doesn't has a spec field, will fail with error.
    If the component is in the obj spec.components, it will be updated directly;
    otherwise, it will be appended to the spec.components list.
    """
    if obj is None:
        module.fail_json(
            msg=f'failed to set enablement status of component {component_name} in None object')
        return
    if obj.get('spec') is None:
        module.fail_json(
            msg=f'failed to set enablement status of component {component_name} in object {obj}')
        return
    spec = obj.get('spec')
    try:
        if 'overrides' not in spec.keys():
            spec['overrides'] = {}
        overrides = spec['overrides']
        if 'components' not in overrides.keys():
            overrides['components'] = []
        hasComponent = False
        for component in overrides['components']:
            if component.get('name', '') == component_name:
                hasComponent = True
                if component.get('enabled', False) != enabled:
                    component['enabled'] = enabled
        if not hasComponent:
            overrides['components'].append({
                'name': component_name,
                'enabled': enabled,
            })
    except (TypeError, AttributeError) as e:
        module.fail_json(
            msg=f'failed to set enablement status of component {component_name}: {e}', exception=e)
