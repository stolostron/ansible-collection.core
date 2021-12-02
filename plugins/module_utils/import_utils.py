import base64
import logging

import yaml
from jinja2 import Template
from kubernetes import client as k8s_client
from kubernetes import config, dynamic, watch
from kubernetes.client import api_client
from kubernetes.dynamic.exceptions import NotFoundError
import backoff
import polling

MANAGEDCLUSTER_TEMPLATE=Template("""
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
""")

KLUSTERLETADDONCONFIG_TEMPLATE=Template("""
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
""")


def should_import(managedcluster):
    conditions = managedcluster['status'].get('conditions', [])
    for condition in conditions:
        if condition['type'] == 'ManagedClusterJoined':
            return False
    return True

def ensure_managedcluster(hub_client, cluster_name):
    managedcluster_api = hub_client.resources.get(api_version="cluster.open-cluster-management.io/v1", kind="ManagedCluster")

    def check_response(response):
        return response['status']

    try:
        managedcluster = managedcluster_api.get(name=cluster_name)
    except NotFoundError:
        new_managedcluster_raw = MANAGEDCLUSTER_TEMPLATE.render(managedcluster_name=cluster_name)
        new_managedcluster = yaml.safe_load(new_managedcluster_raw)
        managedcluster_api.create(new_managedcluster)
        managedcluster = polling.poll(
            target=lambda: managedcluster_api.get(name=cluster_name),
            check_success=check_response,
            step=1,
            timeout=60,
        )
    return managedcluster

def ensure_klusterletaddonconfig(hub_client, eks_cluster_name, addons):
    klusterletaddonconfig_api = hub_client.resources.get(api_version="agent.open-cluster-management.io/v1", kind="KlusterletAddonConfig")
    try:
        klusterletaddonconfig = klusterletaddonconfig_api.get(name=eks_cluster_name, namespace=eks_cluster_name)
        # TODO: ensure klusterletaddonconfig match params[addons] and patch if needed
    except NotFoundError:
        new_klusterletaddonconfig_raw = KLUSTERLETADDONCONFIG_TEMPLATE.render(
            ocm_managedcluster_name=eks_cluster_name, 
            ocm_iam_policy_controller=addons['iam_policy_controller'],
            ocm_search_controller=addons['search_collector'],
            ocm_policy_controller=addons['policy_controller'],
            ocm_cert_policy_controller=addons['cert_policy_controller'],
            ocm_application_manager=addons['application_manager'],
        )
        new_klusterletaddonconfig = yaml.safe_load(new_klusterletaddonconfig_raw)
        klusterletaddonconfig_api.create(new_klusterletaddonconfig)
        klusterletaddonconfig = klusterletaddonconfig_api.get(name=eks_cluster_name, namespace=eks_cluster_name)
    return klusterletaddonconfig

# TODO possibly make this work
# def get_with_retry(api, *backoff_params, **get_params):
#     print(str(get_params))
#     return (backoff.on_exception(*backoff_params))(api.get(name=get_params['name'], namespace=get_params["namespace"]))

@backoff.on_exception(backoff.expo, NotFoundError)
def get_import_secret(secret_api, cluster_name):
    return secret_api.get(name=cluster_name+"-import", namespace=cluster_name)

def get_import_yamls(hub_client, cluster_name):
    #wait for import secret to be generated
    secret_api = hub_client.resources.get(api_version="v1", kind="Secret")
    # import_secret = get_with_retry(secret_api, backoff.expo, NotFoundError, name=cluster_name+"-import", namespace=cluster_name)
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
    object_api_client = dynamic_client.resources.get(
      api_version=resource_dict['apiVersion'], 
      kind=resource_dict['kind']
    )

    try:
      object_api_client.create(resource_dict)
    except:
      pass
