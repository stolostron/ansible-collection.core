from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
name: ocm_managedcluster

plugin_type: inventory

short_description: OCM managedcluster inventory

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"

description:
- Fetch ocm managedclusters, and group clusters by labels.
- Hub cluster information will be stored in the "hub" group.

options:
    plugin:
        description: token that ensures this is a source file for the 'ocm' plugin.
        required: True
        type: str
    hub_kubeconfig:
        description:
        - Path to an existing Kubernetes config file to connect to the hub. If not provided, and no other connection
            options are provided, the Kubernetes client will attempt to load the default
            configuration file from I(~/.kube/config). Can also be specified via K8S_AUTH_KUBECONFIG
            environment variable.
        type: str
        required: False
    cluster_groups:
        description:
        - Optional list of cluster selection settings.
        type: list
        required: False
        suboptions:
            name:
                description:
                - Required name to assign to the group of clusters. The name "hub" is reserved. Name has to be different from cluster names.
                type: str
                required: True
            label_selectors:
                description:
                - A list of key=value strings to filter the managedclusters. Only clusters match all label selectors will be returned in the group.
                    If not provided, all clusters will be included.
                type: list
                required: False
'''

EXAMPLES = r'''
plugin: stolostron.core.ocm_managedcluster
hub_kubeconfig: /path/to/hub/kubeconfig
cluster_groups:
- name: east-region-clusters
  label_selectors:
  - region=us-east-1
- name: aws-clusters
  label_selectors:
  - cloud=Amazon
- name: ocp-clusters
  label_selectors:
  - vendor=OpenShift
- name: add-clusters
'''

import sys
import traceback
IMP_ERR = {}
try:
    import kubernetes
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable


class OCMInventoryException(Exception):
    pass


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    # used internally by Ansible, it should match the file name but not required
    NAME = 'ocm_managedcluster'

    def verify_file(self, path):
        ''' return true/false if this is possibly a valid file for this plugin to consume '''
        valid = False
        if super().verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith(('.yaml', '.yml')):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        super().parse(inventory, loader, path)
        cache_key = self._get_cache_prefix(path)
        self._read_config_data(path)
        self.setup(cache, cache_key)

    def setup(self, cache, cache_key):
        cluster_groups = self.get_option("cluster_groups")
        hub_connection = self.get_option("hub_kubeconfig")
        # add hub entry
        hub_host_name = 'local-cluster'
        self.inventory.add_host(hub_host_name)
        self.inventory.add_group('hub')
        self.inventory.add_child('hub', hub_host_name)
        self.inventory.set_variable(
            hub_host_name, 'cluster_name', 'local-cluster')

        if not hub_connection:
            import os
            # fallback to use env var
            hub_connection = os.getenv('K8S_AUTH_KUBECONFIG')
        else:
            # only set kubeconfig to hub's hostvar if it's provided specifically by user
            self.inventory.set_variable(hub_host_name, 'kubeconfig', hub_connection)

        self.inventory.set_variable("all", "ansible_python_interpreter", sys.executable)
        if IMP_ERR:
            raise OCMInventoryException(IMP_ERR)
        self.fetch_objects(cluster_groups, hub_connection)

    def fetch_objects(self, cluster_groups, hub_connection):
        known_groups = []
        client = None
        # TODO: detect invalid hub kubeconfig
        if hub_connection:
            # get client from hub_connection
            kubernetes.config.load_kube_config(config_file=hub_connection)
            client = kubernetes.dynamic.DynamicClient(
                kubernetes.client.api_client.ApiClient()
            )
        else:
            # get client from system default
            kubernetes.config.load_kube_config()
            client = kubernetes.dynamic.DynamicClient(
                kubernetes.client.api_client.ApiClient()
            )

        # add groups
        if cluster_groups:
            for cluster_group in cluster_groups:
                if not cluster_group.get("name"):
                    raise OCMInventoryException(
                        "Expecting name of cluster_group to be defined."
                    )
                group_name = cluster_group.get("name")
                if group_name == "" or group_name == "hub":
                    raise OCMInventoryException(
                        "Expecting group_name to be not empty, and it cannot be hub."
                    )

                # create a new group
                if group_name not in known_groups:
                    self.inventory.add_group(group_name)
                    known_groups.append(group_name)

                # select clusters base on the given label selectors
                # TODO: use managedclusterview instead of managedcluster to support rbac users
                v1_managedclusters = client.resources.get(
                    api_version="cluster.open-cluster-management.io/v1", kind="ManagedCluster")
                label_selectors = ",".join(
                    cluster_group.get("label_selectors", {}))

                obj = v1_managedclusters.get(label_selector=label_selectors)
                for c in obj.items:
                    host_name = c.metadata.name
                    if host_name in known_groups:
                        raise OCMInventoryException(
                            f"Expecting the host name {c.metadata.name} to be different from group name."
                        )
                    # add host will add an entry to the 'all' group
                    self.inventory.add_host(host_name)
                    self.inventory.add_child(group_name, host_name)
                    self.inventory.set_variable(
                        host_name, 'cluster_name', c.metadata.name)
