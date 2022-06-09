.. Document meta

:orphan:

.. Anchors

.. _ansible_collections.stolostron.core.ocm_managedcluster_inventory:

.. Anchors: short name for ansible.builtin

.. Anchors: aliases



.. Title

stolostron.core.ocm_managedcluster -- OCM managedcluster inventory
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This plugin is part of the `stolostron.core collection <https://galaxy.ansible.com/stolostron/core>`_ (version 0.0.1).

    To install it use: :code:`ansible-galaxy collection install stolostron.core`.

    To use it in a playbook, specify: :code:`stolostron.core.ocm_managedcluster`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Fetch ocm managedclusters, and group clusters by labels.
- Hub cluster information will be stored in the "hub" group.


.. Aliases


.. Requirements


.. Options

Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                            <th>Configuration</th>
                        <th width="100%">Comments</th>
        </tr>
                    <tr>
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-cluster_groups"></div>
                    <b>cluster_groups</b>
                    <a class="ansibleOptionLink" href="#parameter-cluster_groups" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>                                            </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                    <td>
                                                                                            </td>
                                                <td>
                                            <div>Optional list of cluster selection settings.</div>
                                                        </td>
            </tr>
                                        <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-cluster_groups/label_selectors"></div>
                    <b>label_selectors</b>
                    <a class="ansibleOptionLink" href="#parameter-cluster_groups/label_selectors" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">list</span>
                         / <span style="color: purple">elements=string</span>                                            </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                    <td>
                                                                                            </td>
                                                <td>
                                            <div>A list of key=value strings to filter the managedclusters. Only clusters match all label selectors will be returned in the group. If not provided, all clusters will be included.</div>
                                                        </td>
            </tr>
                                <tr>
                                                    <td class="elbow-placeholder"></td>
                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-cluster_groups/name"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-cluster_groups/name" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                    <td>
                                                                                            </td>
                                                <td>
                                            <div>Required name to assign to the group of clusters. The name &quot;hub&quot; is reserved. Name has to be different from cluster names.</div>
                                                        </td>
            </tr>
                    
                                <tr>
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-hub_kubeconfig"></div>
                    <b>hub_kubeconfig</b>
                    <a class="ansibleOptionLink" href="#parameter-hub_kubeconfig" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                    <td>
                                                                                            </td>
                                                <td>
                                            <div>Path to an existing Kubernetes config file to connect to the hub. If not provided, and no other connection options are provided, the Kubernetes client will attempt to load the default configuration file from <em>~/.kube/config</em>. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="parameter-plugin"></div>
                    <b>plugin</b>
                    <a class="ansibleOptionLink" href="#parameter-plugin" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                    <td>
                                                                                            </td>
                                                <td>
                                            <div>token that ensures this is a source file for the &#x27;ocm&#x27; plugin.</div>
                                                        </td>
            </tr>
                        </table>
    <br/>

.. Notes


.. Seealso


.. Examples

Examples
--------

.. code-block:: yaml+jinja

    
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




.. Facts


.. Return values


..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Hao Liu (@TheRealHaoLiu)
- Hanqiu Zhang (@hanqiuzh)
- Nathan Weatherly (@nathanweatherly)



.. Parsing errors

