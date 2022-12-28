#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: managedcluster_info

short_description: Retrieve information about one or more managed clusters from the hub

author:
- "Maxim Babushkin (@MaxBab)"

description:
- Retrieve information about managed clusters from the Hub.

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: str
        required: True
    cluster:
        description: Restrict results by specific cluster.
        type: str
        required: False
'''

EXAMPLES = r'''
- name: "Retrieve information for all managed clusters"
  stolostron.core.managedcluster_info:
    hub_kubeconfig: /path/to/hub/kubeconfig

- name: "Retrieve information for specific managed cluster"
  stolostron.core.managedcluster_info:
    hub_kubeconfig: /path/to/hub/kubeconfig
    cluster: cluster_name
'''

RETURN = r'''
results:
  type: complex
  description: A dictionary of results output
  returned: success
  contains:
    name:
      description: Managed cluster name
      type: str
      returned: success
    version:
      description: Version of the cluster
      type: str
      returned: success
    labels:
      description: Dict of cluster labels
      type: dict
      returned: success
    cluster_claims:
      description: The cluster claims
      type: dict
      returned: success
    conditions:
      description: Conditions state of the cluster
      type: list
      returned: success
'''

import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib

IMP_ERR = {}
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}


def parse_labels(data):
    label_dict = {}

    for label in data:
        label_dict[label[0]] = label[1]

    return label_dict


def parse_cluster_claims(data):
    claim_dict = {}

    for claim in data:
        claim_dict[claim["name"]] = claim["value"]

    return claim_dict


def parse_conditions(data):
    condition_list = []

    for condition in data:
        condition_list.append(
            {"type": condition["type"],
             "reason": condition["reason"],
             "message": condition["message"],
             "status": condition["status"]}
        )

    return condition_list


def execute_module(module: AnsibleModule):
    results = []

    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])

    cluster = module.params['cluster']
    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )

    v1_managedclusters = hub_client.resources.get(
        api_version="cluster.open-cluster-management.io/v1", kind="ManagedCluster")
    cluster_selection = ""
    if cluster:
        cluster_selection = f"name={cluster}"

    obj = v1_managedclusters.get(label_selector=cluster_selection)
    for cl in obj.items:
        results.append(
            {"name": cl.metadata.name,
             "labels": parse_labels(cl.metadata.labels),
             "cluster_claims": parse_cluster_claims(cl.status.clusterClaims),
             "conditions": parse_conditions(cl.status.conditions),
             "version": cl.status.version.kubernetes}
        )

    module.exit_json(changed=False, results=results)


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='str', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        cluster=dict(type='str', required=False),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    execute_module(module)


if __name__ == '__main__':
    main()
