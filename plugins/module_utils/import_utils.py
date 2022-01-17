from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

# TODO: learn from other module import error handling and come up with an convention
import base64
import traceback

IMP_ERR = {}
try:
    import yaml
except ImportError as e:
    IMP_ERR['yaml'] = {'error': traceback.format_exc(),
                       'exception': e}
try:
    from kubernetes.dynamic import DynamicClient
    from kubernetes.dynamic.exceptions import DynamicApiError, NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}
try:
    from jinja2 import Template
except ImportError as e:
    IMP_ERR['jinja2'] = {'error': traceback.format_exc(),
                         'exception': e}
from ansible.errors import AnsibleError

MANAGEDCLUSTER_TEMPLATE = """
apiVersion: cluster.open-cluster-management.io/v1
kind: ManagedCluster
metadata:
  name: {{ managedcluster_name }}
labels:
  name: {{ managedcluster_name }}
  vendor: auto-detect
  cloud: auto-detect
spec:
  hubAcceptsClient: true
  leaseDurationSeconds: 60
"""

KLUSTERLETADDONCONFIG_TEMPLATE = """
---
apiVersion: agent.open-cluster-management.io/v1
kind: KlusterletAddonConfig
metadata:
  name: {{ ocm_managedcluster_name }}
  namespace: {{ ocm_managedcluster_name }}
spec:
  clusterName: {{ ocm_managedcluster_name }}
  clusterNamespace: {{ ocm_managedcluster_name }}
  clusterLabels:
    cloud: auto-detect
    name: {{ ocm_managedcluster_name }}
    vendor: auto-detect
  iamPolicyController:
    enabled: {{ ocm_iam_policy_controller }}
  searchCollector:
    enabled: {{ ocm_search_controller }}
  policyController:
    enabled: {{ ocm_policy_controller }}
  certPolicyController:
    enabled: {{ ocm_cert_policy_controller }}
  applicationManager:
    enabled: {{ ocm_application_manager }}
"""


def should_import(managedcluster):
    """
    should_import returns True if the input managedCluster should be imported,
    and False if otherwise.
    :param managedcluster: name of managedCluster to import
    :return: bool
    """
    conditions = managedcluster['status'].get('conditions', [])
    for condition in conditions:
        if condition['type'] == 'ManagedClusterJoined':
            return False
    return True


def ensure_managedcluster(hub_client, cluster_name, timeout):
    """
    ensure_managedcluster checks and waits until the managedCluster is successfully imported.
    :param hub_client: the ACM Hub cluster's API client
    :param cluster_name: name of the managedCluster to check
    :param timeout: number of seconds to wait for managedcluster status field to be available
    :return: the managedCluster object
    """
    managedcluster_api = hub_client.resources.get(
        api_version="cluster.open-cluster-management.io/v1",
        kind="ManagedCluster")

    try:
        managedcluster = managedcluster_api.get(name=cluster_name)
    except NotFoundError:
        if 'jinja2' in IMP_ERR:
            raise AnsibleError("Error importing Kubernetes: " + IMP_ERR['k8s']['error'])
        if 'yaml' in IMP_ERR:
            raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error'])
        new_managedcluster_raw = Template(MANAGEDCLUSTER_TEMPLATE).render(managedcluster_name=cluster_name)
        new_managedcluster = yaml.safe_load(new_managedcluster_raw)
        managedcluster_api.create(new_managedcluster)
        if not wait_until_resource_status_available(managedcluster_api, None, cluster_name, timeout):
            raise AnsibleError("Error timed out waiting for managedcluster {0} status field to be available".format(cluster_name))
        managedcluster = managedcluster_api.get(name=cluster_name)

    return managedcluster


def ensure_klusterletaddonconfig(hub_client, eks_cluster_name, addons, timeout):
    """
    ensure_klusterletaddonconfig creates the Klusterlet addon config if it's
    not already existed, and returns the config object.
    :param hub_client: dynamic client for the ACM hub cluster
    :param eks_cluster_name: name of EKS cluster
    :param addons: a dict of all addons and whether they are enabled/disabled
    :param timeout: number of seconds to wait for klusterletaddonconfig to be available
    :return: the Klusterlet addon config object
    """
    if 'k8s' in IMP_ERR:
        raise AnsibleError("Error importing Kubernetes: " + IMP_ERR['k8s']['error'])
    klusterletaddonconfig_api = hub_client.resources.get(
        api_version="agent.open-cluster-management.io/v1",
        kind="KlusterletAddonConfig")
    try:
        klusterletaddonconfig = klusterletaddonconfig_api.get(name=eks_cluster_name,
                                                              namespace=eks_cluster_name)
        # TODO: ensure klusterletaddonconfig match params[addons] and patch if needed
    except NotFoundError:
        if 'jinja2' in IMP_ERR:
            raise AnsibleError("Error importing Kubernetes: " + IMP_ERR['k8s']['error'])
        if 'yaml' in IMP_ERR:
            raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error'])
        new_klusterletaddonconfig_raw = Template(KLUSTERLETADDONCONFIG_TEMPLATE).render(
            ocm_managedcluster_name=eks_cluster_name,
            ocm_iam_policy_controller=addons['iam_policy_controller'],
            ocm_search_controller=addons['search_collector'],
            ocm_policy_controller=addons['policy_controller'],
            ocm_cert_policy_controller=addons['cert_policy_controller'],
            ocm_application_manager=addons['application_manager'],
        )
        new_klusterletaddonconfig = yaml.safe_load(new_klusterletaddonconfig_raw)
        klusterletaddonconfig_api.create(new_klusterletaddonconfig)
        if not wait_until_resource_available(klusterletaddonconfig_api, None, eks_cluster_name, timeout):
            raise AnsibleError("Error timed out waiting for klusterletaddonconfig {0} to be available".format(eks_cluster_name))
        klusterletaddonconfig = klusterletaddonconfig_api.get(name=eks_cluster_name,
                                                              namespace=eks_cluster_name)
    return klusterletaddonconfig


def get_import_yamls(hub_client, cluster_name, timeout):
    """
    Generates the yamls files for importing a managed cluster into an ACM hub cluster
    :param hub_client: The dynamic Kubernetes client based on the user provided ACM hub kubeconfig
    :param cluster_name: The name of the managed cluster to import
    :param timeout: number of seconds to wait for secret to be available
    :return: [yaml as a dict for CRDs, list of yamls as dicts for import objects]
    """
    if 'yaml' in IMP_ERR:
        raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error'])
    # Wait for import secret to be generated
    secret_api = hub_client.resources.get(api_version="v1", kind="Secret")
    secret_name = "{0}-import".format(cluster_name)
    if not wait_until_secret_populated(secret_api, cluster_name, secret_name, timeout):
        raise AnsibleError("Error timed out waiting for secret {0} to be populated".format(secret_name))
    import_secret = secret_api.get(name=secret_name, namespace=cluster_name)

    crds_yaml_b64_str = import_secret['data']['crds.yaml']
    crds_yaml_b64_bytes = crds_yaml_b64_str.encode('ascii')
    crds_yaml_bytes = base64.b64decode(crds_yaml_b64_bytes)
    crds_yaml = crds_yaml_bytes.decode('ascii')
    crds_yaml_ret = yaml.safe_load(crds_yaml)

    import_yaml_b64_str = import_secret['data']['import.yaml']
    import_yaml_b64_bytes = import_yaml_b64_str.encode('ascii')
    import_yaml_bytes = base64.b64decode(import_yaml_b64_bytes)
    import_yaml = import_yaml_bytes.decode('ascii')
    import_yaml_ret = yaml.safe_load_all(import_yaml)

    return crds_yaml_ret, import_yaml_ret


def dynamic_apply(dynamic_client, resource_dict):
    """
    Applying resources with the provided dynamic client
    :param dynamic_client: Dynamic client
    :param resource_dict: resource as a dict
    :return: None
    """
    if 'k8s' in IMP_ERR:
        raise AnsibleError("Error importing Kubernetes: " + IMP_ERR['k8s']['error'])
    object_api_client = dynamic_client.resources.get(
        api_version=resource_dict['apiVersion'],
        kind=resource_dict['kind']
    )

    try:
        object_api_client.create(resource_dict)
    except DynamicApiError as exc:
        # TODO retry depending on error type
        raise AnsibleError(f'Failed to create object: {exc.body}')


def get_managed_cluster(hub_client: DynamicClient, managed_cluster_name: str):
    managed_cluster_api = hub_client.resources.get(
        api_version="cluster.open-cluster-management.io/v1",
        kind="ManagedCluster",
    )

    try:
        managed_cluster = managed_cluster_api.get(name=managed_cluster_name)
    except NotFoundError:
        return None

    return managed_cluster

def is_namespace_exists(dynamic_client, namespace):
    """
    Check if namespace exists
    :param dynamic_client: Dynamic client
    :param namespace: The name of the namespace
    :return: True if namespace exists, False if namespace does not exists.
    """
    namespace_api = dynamic_client.resources.get(
        api_version="v1",
        kind="Namespace",
    )

    try:
        ns = namespace_api.get(name=namespace)
        return True
    except NotFoundError:
        return False

def wait_until_resource_available(resource_api, namespace, name, timeout: int=60):
    """
    Block until the given resource is available (or timeout)
    :param resource_api: The API resource object that will be used to query the API
    :param namespace: The namespace to query
    :param name: The name of the resource to query
    :param timeout: The amount of time in seconds to wait before terminating the query
    :return: True if resource is available, False if a timeout occured.
    """
    for event in resource_api.watch(namespace=namespace, timeout=timeout):
        if event["type"] == "ADDED" and event["object"].metadata.name == name:
            return True

    return False


def wait_until_resource_status_available(resource_api, namespace, name, timeout: int=60):
    """
    Block until the given resource status field is available (or timeout)
    :param resource_api: The API resource object that will be used to query the API
    :param namespace: The namespace to query
    :param name: The name of the resource to query
    :param timeout: The amount of time in seconds to wait before terminating the query
    :return: True if resource status field is available, False if a timeout occured.
    """
    for event in resource_api.watch(namespace=namespace, timeout=timeout):
        if event["type"] in ["ADDED", "MODIFIED"] and event["object"].metadata.name == name:
            if "status" in event["object"].keys():
                return True

    return False


def wait_until_managedcluster_joined(resource_api, cluster_name, timeout: int=60):
    """
    Block until the given managedcluster joined (or timeout)
    :param resource_api: The API resource object that will be used to query the API
    :param cluster_name: The name of the managedcluster to query
    :param timeout: The amount of time in seconds to wait before terminating the query
    :return: True if managedcluster joined, False if a timeout occured.
    """
    joined = False
    for event in resource_api.watch(timeout=timeout):
        if event["type"] in ["ADDED", "MODIFIED"] and event["object"].metadata.name == cluster_name:
            if "status" in event["object"].keys():    
                conditions = event["object"]["status"].get("conditions", [])
                for condition in conditions:
                    if condition["type"] == "ManagedClusterJoined":
                        joined = True
                        break
            if joined:
                break

    return joined


def wait_until_secret_populated(resource_api, namespace, secret_name, timeout: int=60):
    """
    Block until the given secret populated (or timeout)
    :param resource_api: The API resource object that will be used to query the API
    :param namespace: The namespace to query
    :param secret_name: The name of the secret to query
    :param timeout: The amount of time in seconds to wait before terminating the query
    :return: True if secret populated, False if a timeout occured.
    """
    for event in resource_api.watch(namespace=namespace, timeout=timeout):
        if event["type"] in ["ADDED", "MODIFIED"] and event["object"].metadata.name == secret_name:
            if "data" in event["object"].keys() and "crds.yaml" in event["object"]["data"].keys() and "import.yaml" in event["object"]["data"].keys():
                return True
    return False

    

