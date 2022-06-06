#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: cluster_proxy

short_description: cluster proxy

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"

description:
- Install the cluster proxy on a managedcluster, and get proxy url from the addon. cluster-admin permission
    on hub is assumed to enable the plugin.

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
  stolostron.core.cluster_proxy:
    hub_kubeconfig: /path/to/hub/kubeconfig
    managed_cluster: example-cluster
  register: cluster_proxy_url
'''

RETURN = r'''
msg:
    description: human readable message describing the cluster proxy is ready or not.
    returned: always
    type: str
cluster_url:
    description: Host url of cluster proxy
    returned: when cluster proxy is enabled and available
    type: str
    sample: "https://cluster-proxy-user.apps.example.com/cluster-name"
exception:
    description: exception catched during the process.
    returned: when exception is catched
    type: complex
    contains: {}
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible_collections.stolostron.core.plugins.module_utils.import_utils import get_managed_cluster
from ansible_collections.stolostron.core.plugins.module_utils.addon_utils import check_addon_available

IMP_ERR = {}
try:
    from kubernetes.dynamic.exceptions import NotFoundError
    import kubernetes
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}

try:
    import requests
except ImportError as e:
    IMP_ERR['requests'] = {'error': traceback.format_exc(),
                           'exception': e}

try:
    import urllib3
except ImportError as e:
    IMP_ERR['urllib3'] = {'error': traceback.format_exc(),
                          'exception': e}


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
                                       status_forcelist=[400, 500, 502, 503, 504])
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

    wait = module.params['wait']
    timeout = module.params['timeout']
    if timeout is None or timeout <= 0:
        timeout = 60
    managed_cluster = get_managed_cluster(hub_client, managed_cluster_name)
    if managed_cluster is None:
        # TODO: throw error and exit
        module.fail_json(msg=f"managedcluster {managed_cluster_name} not found",
                         exception=f"failed to get managedcluster {managed_cluster_name} not found")
        # TODO: there might be other exit condition

    addon_name = 'cluster-proxy'
    if not check_addon_available(hub_client, managed_cluster_name, addon_name):
        module.fail_json(
            msg=f'failed to check addon: {addon_name} of {managed_cluster_name} is not available')

    ocm_namespace = get_ocm_install_namespace(hub_client)
    if ocm_namespace is None:
        module.fail_json(msg="failed to detect ocm namespace")

    hub_proxy_url = get_hub_proxy_route(hub_client, ocm_namespace)
    if hub_proxy_url == "" or hub_proxy_url is None:
        module.fail_json(msg="failed to get hub proxy url")

    cluster_url = f"https://{hub_proxy_url}/{managed_cluster_name}"
    health_url = f"{cluster_url}/healthz"
    if wait:
        if not wait_for_proxy_route_available(health_url, timeout):
            module.fail_json(
                msg=f"timed out waiting for proxy url {health_url} to become available")

    module.exit_json(cluster_url=cluster_url,
                     msg=f'cluster proxy is ready at {cluster_url}.')


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
