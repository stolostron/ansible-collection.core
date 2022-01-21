#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: cluster_proxy_addon

short_description: cluster proxy addon

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"

description: Install the cluster proxy addon, and get proxy url from the addon. cluster-admin permission on hub is assumed to enable the plugin.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    wait:
        description: Whether to wait for clusters to show up as managed clusters
        type: bool
        default: False
        required: False
    timeout:
        description: Number of seconds to wait for the addons to show up
        type: int
        default: 60
        required: False
    managed_cluster:
        description: Name of managed cluster to
        type: str
        required: True
'''

EXAMPLES = r'''
- name: "Get proxy cluster url for example-cluster"
  ocmplus.cm.cluster_proxy_addon:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
  register: cluster_proxy_url
'''

RETURN = r'''
cluster_url:
    description: Host url of cluster proxy
    returned: when cluster proxy is enabled and available
    type: str
    sample: "https://cluster-proxy-user.apps.example.com/cluster-name"
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import traceback
import requests
import urllib3

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.ocmplus.cm.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.ocmplus.cm.plugins.module_utils.addon_utils import (
    ensure_managed_cluster_addon_enabled,
    wait_for_addon_available,
)

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError
    import kubernetes
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def ensure_cluster_proxy_feature_enabled(hub_client) -> dict:
    # get all instance of mch
    mch_api = hub_client.resources.get(
        api_version="operator.open-cluster-management.io/v1",
        kind="MultiClusterHub",
    )

    mch_list = mch_api.get()
    if len(mch_list.get('items', [])) != 1:
        # TODO: throw error
        return mch_list

    mch = mch_list.items[0]
    if mch.spec.enableClusterProxyAddon:
        return mch

    mch.spec.enableClusterProxyAddon = True
    mch = mch_api.patch(
        name=mch.metadata.name,
        namespace=mch.metadata.namespace,
        body=mch_list.to_dict()['items'][0],
        content_type="application/merge-patch+json",
    )

    return mch


def get_hub_proxy_route(hub_client, ocm_namespace: str):
    route_api = hub_client.resources.get(
        api_version="route.openshift.io/v1", kind="Route")
    try:
        route = route_api.get(
            name='cluster-proxy-addon-user', namespace=ocm_namespace)
    except NotFoundError:
        return None
    return route.spec.host


def wait_for_proxy_route_available(url, timeout=60):
    max_retry = 5
    retries = urllib3.util.retry.Retry(total=max_retry,
                                       backoff_factor=timeout /
                                       max_retry / (max_retry + 1),
                                       status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.mount(
        'https://', requests.adapters.HTTPAdapter(max_retries=retries))
    try:
        session.get(url, verify=False)
        return True
    except requests.exceptions.RetryError as e:
        return False


def get_ocm_install_namespace(hub_client):
    mch_api = hub_client.resources.get(
        api_version="operator.open-cluster-management.io/v1",
        kind="MultiClusterHub",
    )

    mch_list = mch_api.get()
    if len(mch_list.get('items', [])) != 1:
        return None
    mch = mch_list.items[0]
    return mch.metadata.namespace


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    managed_cluster_name = module.params['managed_cluster']

    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )

    timeout = module.params['timeout']
    managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
    if managed_cluster is None:
        # TODO: throw error and exit
        module.fail_json(f"managedcluster {managed_cluster_name} not found",
                         err=f"failed to get managedcluster {managed_cluster_name} not found")
        # TODO: there might be other exit condition

    ensure_cluster_proxy_feature_enabled(hub_client)
    cluster_proxy_addon = ensure_managed_cluster_addon_enabled(
        module, hub_client, "cluster-proxy", managed_cluster_name, "open-cluster-management-agent-addon")

    wait = module.params['wait']
    if wait:
        wait_for_addon_available(
            module, hub_client, cluster_proxy_addon, timeout)

    ocm_namespace = get_ocm_install_namespace(hub_client)
    if ocm_namespace is None:
        module.fail_json("failed to detect ocm namespace",
                         err="failed to detect ocm namespace")

    hub_proxy_url = get_hub_proxy_route(hub_client, ocm_namespace)
    if hub_proxy_url == "" or hub_proxy_url is None:
        module.fail_json("failed to get hub proxy url",
                         err="failed to get hub proxy url")

    cluster_url = f"https://{hub_proxy_url}/{managed_cluster_name}"
    health_url = f"{cluster_url}/healthz"
    if wait:
        if not wait_for_proxy_route_available(health_url, timeout):
            module.fail_json(f"timed out waiting for proxy url {health_url} to become available",
                             err=f"timed out waiting for proxy url {health_url} to become available")

    module.exit_json(cluster_url=cluster_url)


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        managed_cluster=dict(type='str', required=True),
        wait=dict(type='bool', required=False, default=False),
        timeout=dict(type='int', required=False, default=60)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
