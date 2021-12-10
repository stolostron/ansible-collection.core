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


def ensure_managedcluster(hub_client, cluster_name):
    """
    ensure_managedcluster checks and polls until the managedCluster is successfully imported.
    :param hub_client: the ACM Hub cluster's API client
    :param cluster_name: name of the managedCluster to check
    :return: the managedCluster object
    """
    managedcluster_api = hub_client.resources.get(
        api_version="cluster.open-cluster-management.io/v1",
        kind="ManagedCluster")

    def check_response(response):
        return response['status']

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
        try:
            import polling
            managedcluster = polling.poll(
                target=lambda: managedcluster_api.get(name=cluster_name),
                check_success=check_response,
                step=1,
                timeout=60,
            )
        except ImportError:
            pass
    return managedcluster


def ensure_klusterletaddonconfig(hub_client, eks_cluster_name, addons):
    """
    ensure_klusterletaddonconfig creates the Klusterlet addon config if it's
    not already existed, and returns the config object.
    :param hub_client: dynamic client for the ACM hub cluster
    :param eks_cluster_name: name of EKS cluster
    :param addons: a dict of all addons and whether they are enabled/disabled
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
        klusterletaddonconfig = klusterletaddonconfig_api.get(name=eks_cluster_name,
                                                              namespace=eks_cluster_name)
    return klusterletaddonconfig


try:
    import backoff

    @backoff.on_exception(backoff.expo, NotFoundError)
    def get_import_secret(secret_api, cluster_name):
        """
        Fetches the managed cluster import secret with exponential backoff
        :param secret_api: The Secret API from the ACM hub client
        :param cluster_name: The name of managed cluster
        :return: The Secret object
        """
        return secret_api.get(name=cluster_name + "-import", namespace=cluster_name)
except ImportError:
    raise AnsibleError("Error importing backoff lib: " + traceback.format_exc())


def get_import_yamls(hub_client, cluster_name):
    """
    Generates the yamls files for importing a managed cluster into an ACM hub cluster
    :param hub_client: The dynamic Kubernetes client based on the user provided ACM hub kubeconfig
    :param cluster_name: The name of the managed cluster to import
    :return: [yaml as a dict for CRDs, list of yamls as dicts for import objects]
    """
    if 'yaml' in IMP_ERR:
        raise AnsibleError("Error importing yaml: " + IMP_ERR['yaml']['error'])
    # Wait for import secret to be generated
    secret_api = hub_client.resources.get(api_version="v1", kind="Secret")
    import_secret = get_import_secret(secret_api, cluster_name)

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
