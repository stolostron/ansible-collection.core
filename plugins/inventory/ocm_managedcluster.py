# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

DOCUMENTATION = r"""
name: ocm_managedcluster

plugin_type: inventory

short_description: OCM managedcluster inventory

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Philip Douglass (@philipsd6)"

description:
- Fetch ocm managedclusters, and group clusters by labels.
- Hub cluster information will be stored in the "hub" group.

extends_documentation_fragment:
- constructed
- inventory_cache
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
"""

EXAMPLES = r"""
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
"""

try:
    import kubernetes

    HAS_KUBERNETES = True
except ImportError:
    HAS_KUBERNETES = False

from ansible.errors import AnsibleError, AnsibleParserError
from ansible.inventory.helpers import get_group_vars
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import missing_required_lib
from ansible.plugins.inventory import BaseInventoryPlugin, Cacheable, Constructable
from ansible.utils.vars import combine_vars


class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):
    # used internally by Ansible, it should match the file name but not required
    NAME = "ocm_managedcluster"

    def verify_file(self, path):
        """return true/false if this is possibly a valid file for this plugin to consume"""
        valid = False
        if super().verify_file(path):
            # base class verifies that file exists and is readable by current user
            if path.endswith((".yaml", ".yml")):
                valid = True
        return valid

    def parse(self, inventory, loader, path, cache=True):
        if not HAS_KUBERNETES:
            raise AnsibleError(missing_required_lib("kubernetes"))
        super().parse(inventory, loader, path, cache)
        self._read_config_data(path)

        # 'cache' may be True or False depending on if the inventory is being refreshed;
        # the user's cache option indicates if we should save the cache if it's changing.
        user_cache_setting = self.get_option("cache")
        # Read from cache if the user has caching enabled and the cache isn't being refreshed
        self.attempt_to_read_cache = user_cache_setting and cache
        # Update if the user has caching enabled and the cache is being refreshed;
        self.cache_needs_update = user_cache_setting and not cache

        self.setup()
        self.populate()

        # Add support for Constructable options
        strict = self.get_option("strict", False)

        for host in self.inventory.hosts:
            hostvars = combine_vars(
                get_group_vars(self.inventory.hosts[host].get_groups()),
                self.inventory.hosts[host].get_vars(),
            )
            # Create composite vars
            self._set_composite_vars(
                self.get_option("compose"), hostvars, host, strict=strict
            )

            # refetch host vars in case new ones have been created above
            hostvars = combine_vars(
                get_group_vars(self.inventory.hosts[host].get_groups()),
                self.inventory.hosts[host].get_vars(),
            )

            # Constructed groups based on conditionals
            self._add_host_to_composed_groups(
                self.get_option("groups"), hostvars, host, strict=strict
            )

            # Constructed keyed_groups
            self._add_host_to_keyed_groups(
                self.get_option("keyed_groups"), hostvars, host, strict=strict
            )

    def setup(self):
        hub_connection = hub_kubeconfig = self.get_option("hub_kubeconfig")
        if not hub_connection:
            import os

            # fallback to use env var
            hub_connection = os.getenv("K8S_AUTH_KUBECONFIG")

        kubernetes.config.load_kube_config(config_file=hub_connection)
        self.client = kubernetes.dynamic.DynamicClient(
            kubernetes.client.api_client.ApiClient()
        )

        hub_cluster = next(
            iter(self.fetch_clusters(label_selectors="name=local-cluster"))
        )
        hub_host_name = hub_cluster["cluster_name"]
        self.inventory.add_group("hub")
        self.inventory.add_host(hub_host_name, group="hub")
        if hub_kubeconfig:
            # only set kubeconfig to hub's hostvar if it's provided specifically by user
            self.inventory.set_variable(hub_host_name, "kubeconfig", hub_kubeconfig)
        for k, v in hub_cluster.items():
            self.inventory.set_variable(hub_host_name, k, v)

    def extract_hostvars(self, cluster_obj):
        """Extract only relevant data from a managedcluster object"""
        try:
            return {
                "cluster_name": cluster_obj.metadata.name,
                "client_config": dict(
                    next(iter(cluster_obj.spec.managedClusterClientConfigs or []), {})
                ),
                "annotations": {
                    k: v
                    for k, v in cluster_obj.metadata.annotations
                    if not k.endswith("last-applied-configuration")
                },
                "labels": dict(cluster_obj.metadata.labels),
            }
        except:
            return {}

    def fetch_clusters(self, label_selectors=None):
        """Return cluster data from cache or API"""
        if isinstance(label_selectors, list):
            label_selectors = ",".join(label_selectors)
        # TODO: use managedclusterview instead of managedcluster to support rbac users
        resource_api = self.client.resources.get(
            api_version="cluster.open-cluster-management.io/v1", kind="ManagedCluster"
        )

        cache_key = self.get_cache_key(
            f"{resource_api.group_version}/{resource_api.name}?{label_selectors}"
        )
        if self.attempt_to_read_cache:
            try:
                clusters = self._cache[cache_key]
            except KeyError:
                # cache_key isn't cached, or has expired
                self.cache_needs_update = True

        if self.cache_needs_update or not self.attempt_to_read_cache:
            try:
                obj = resource_api.get(label_selector=label_selectors)
                clusters = [self.extract_hostvars(c) for c in obj.items]
            except Exception as e:
                raise AnsibleError("Error while fetching clusters: %s" % to_native(e))

        if self.cache_needs_update:
            self._cache[cache_key] = clusters

        return clusters

    def populate(self):
        """Populate inventory"""
        cluster_groups = self.get_option("cluster_groups") or []
        for cluster_group in cluster_groups:
            group_name = cluster_group.get("name")
            if group_name == "hub":
                raise AnsibleError("group_name cannot be 'hub'")

            label_selectors = ",".join(cluster_group.get("label_selectors", []))
            for c in self.fetch_clusters(label_selectors=label_selectors):
                host_name = c["cluster_name"]
                # This doesn't need to be fatal (Ansible warns about this) but it can
                # lead to unexpected surprises.
                if host_name in self.inventory.groups or host_name == group_name:
                    raise AnsibleParserError(
                        f"Expecting the host name {host_name} to be different from group name."
                    )
                # add host will add an entry to the 'all' group
                self.inventory.add_host(host_name)
                if group_name:
                    self.inventory.add_group(group_name)
                    self.inventory.add_host(host_name, group=group_name)
                    # self.inventory.add_child(group_name, host_name)
                for k, v in c.items():
                    self.inventory.set_variable(host_name, k, v)
