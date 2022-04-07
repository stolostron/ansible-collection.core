from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import traceback
import re

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError, ResourceNotFoundError, UnauthorizedError, ForbiddenError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def get_nested(obj, path_list):
    """
    get_nested will iterate through the path list, and returns the nested object.
    obj is expected to be a dict, and path_list is expected to be a list of string indicating how we can find the target.
    If the target doesn't exist, None will be returned.
    """
    if obj is None:
        return None
    curr = obj
    for p in path_list:
        next = curr.get(p)
        if next is None:
            return None
        curr = next
    return curr


def get_multi_cluster_hub(hub_client, module, ignore_not_found=False, warn_no_permission=False):
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
            module.fail_json(msg=f'failed to list MultiClusterHub: {e}')
        return None
    except (UnauthorizedError, ForbiddenError) as e:
        if not warn_no_permission:
            module.fail_json(msg=f'failed to list MultiClusterHub: {e}')
        else:
            module.warn(f'failed to list MultiClusterHub: {e}')
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
            msg=f'failed to get MultiClusterHub {first_mch.metadata.name} in {first_mch.metadata.namespace} namespace: {e}')

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
                f'failed to get MultiClusterEngine: {e}.')
        return None

    first_mce = mce_list.items[0]
    mce = None
    # get mce directly for return
    try:
        mce = mce_api.get(name=first_mce.metadata.name,
                          namespace=first_mce.metadata.namespace)
    except DynamicApiError as e:
        module.fail_json(
            msg=f'failed to get MultiClusterEngine {first_mce.metadata.name}: {e}')

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
    components = get_nested(obj, obj_feature_path)
    if components is None:
        return False
    try:
        for component in components:
            if component.get('name', '') != component_name:
                continue
            return component.get('enabled', False)
    except (TypeError, AttributeError) as e:
        module.fail_json(
            msg=f'failed to get enablement status of component {component_name}: {e}')

    return False


def get_mch_version(mch):
    """
    get_mch_version returns current version of mch CR.
    """
    if mch is None:
        return None
    mch_version_path = ['status', 'currentVersion']
    version = get_nested(mch, mch_version_path)

    return version


def compare_version(current_version, target_version):
    """
    compare_version compares the current version with the target version, both versions will be semver strings.
    This function returns True if the current version is >= the target version.
    This function only checks major minor and patch versions, the pre-release information will be ignored.
    If the current version is lower, the function returns false.
    This function assumes the target version is always valid.
    If the current version is not valid (e.g. missing minor or patch version), it returns false directly.
    """
    if current_version is None or target_version is None:
        return False
    semver_regex = re.compile(
        r'^(?P<major>0|[1-9]\d*)(\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*).*)')
    curr_match = semver_regex.match(current_version)
    if curr_match is None:
        return False

    target_match = semver_regex.match(target_version)
    if target_match is None:
        return False

    curr = curr_match.groupdict()
    target = target_match.groupdict()
    compare_order = ['major', 'minor', 'patch']
    for field in compare_order:
        curr_num = int(curr.get(field, '0'))
        target_num = int(target.get(field, '0'))
        if curr_num == target_num:
            continue
        elif curr_num < target_num:
            return False
        else:
            return True

    return True


def check_mch_version(hub_client, module, required_version):
    """
    check_mch_version checks if the MCH's current version is >= required_version.
    If the current version is lower than the required_version, the process will fail and exit.
    If the MCH is not found, if a version does not exist in the MCH, or if has no permission, it only shows warnings.
    """
    mch = get_multi_cluster_hub(
        hub_client=hub_client, module=module, ignore_not_found=False, warn_no_permission=True)
    if mch is None:
        module.warn(
            'skipping version check because the MCH cannot be accessed.')
        return
    version = get_mch_version(mch)
    if version is None:
        module.warn(
            'skipping version check because there is no version found in the MCH.')
        return
    if not compare_version(version, required_version):
        module.fail_json(
            msg=f'currenct MCH version {version} is lower than the required version {required_version} for this function.')


def get_csv_version(csv, prefix):
    """
    get_csv_version retuns version as a string by checking a ClusterServiceVersion object.
    It first checks spec.version, and if it's empty, it parses the name by removing the prefix to get the semver.
    This function returns None if failed to find a version.
    """
    if csv is None:
        return None
    spec_version = get_nested(csv, ['spec', 'version'])
    if not (spec_version is None) and len(spec_version) > 0:
        return spec_version
    name = get_nested(csv, ['metadata', 'name'])
    # check if prefix is valid
    if name is None or len(name) < len(prefix) + 2 or name[:len(prefix) + 2] != prefix + '.v':
        return None
    version = name[len(prefix) + 2:]
    if len(version) > 0 and version[0:1].isdigit():
        return version

    return None


def check_mce_version(hub_client, module, required_version, warn_no_permission=True):
    """
    check_mch_version checks if the MCE's current version is >= required_version.
    The version will be grepped from the highest version of the csv in the environment.
    If the current version is lower than the required_version, or if the MCE CSV is not found, the process will fail.
    If has no permission to query CSVs, it will only show warnings.
    """
    try:
        csv_api = hub_client.resources.get(
            api_version="operators.coreos.com/v1alpha1",
            kind="ClusterServiceVersion",
        )
        csv_list = csv_api.get()
    except (UnauthorizedError, ForbiddenError) as e:
        if warn_no_permission:
            module.warn(
                f'failed to list ClusterServiceVersion for MCE version check: {e}')
        else:
            module.fail_json(
                msg=f'failed to list ClusterServiceVersion for MCE version check: {e}')
        return
    except (DynamicApiError) as e:
        module.fail_json(
            msg=f'failed to list ClusterServiceVersion for MCE version check: {e}')
        return
    current_version = None
    # find the one that with mce in it's name
    for item in csv_list.items:
        metadata = item.metadata
        if metadata is None:
            continue
        name = metadata.name
        if name is None:
            continue
        namespace = metadata.namespace
        if namespace is None:
            continue
        if not ('multicluster-engine' in name):
            continue
        try:
            csv = csv_api.get(name=name, namespace=namespace)
        except (DynamicApiError) as e:
            module.fail_json(
                msg=f'failed to get ClusterServiceVersion {name} for MCE version check: {e}')
            return
        version = get_csv_version(csv, 'multicluster-engine')
        if version is None:
            continue
        if current_version is None or compare_version(version, current_version):
            current_version = version
    if current_version is None:
        module.fail_json(
            msg='failed to find the current MCE version from ClusterServiceVersions.')
    if not compare_version(current_version, required_version):
        module.fail_json(
            msg=f'currenct MCE version {current_version} is lower than the required version {required_version} for this function.')


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
            msg=f'failed to set enablement status of component {component_name}: {e}')
