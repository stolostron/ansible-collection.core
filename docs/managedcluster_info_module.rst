.. Document meta

:orphan:

.. Anchors

.. _ansible_collections.stolostron.core.managedcluster_info_module:

.. Anchors: short name for ansible.builtin

.. Anchors: aliases



.. Title

stolostron.core.managedcluster_info -- Retrieve information about one or more managed clusters from the hub
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This plugin is part of the `stolostron.core collection <https://galaxy.ansible.com/stolostron/core>`_ (version 0.0.2).

    To install it use: :code:`ansible-galaxy collection install stolostron.core`.

    To use it in a playbook, specify: :code:`stolostron.core.managedcluster_info`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Retrieve information about managed clusters from the Hub.


.. Aliases


.. Requirements


.. Options

Parameters
----------

.. raw:: html

    <table  border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Parameter</th>
            <th>Choices/<font color="blue">Defaults</font></th>
                        <th width="100%">Comments</th>
        </tr>
                    <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-cluster"></div>
                    <b>cluster</b>
                    <a class="ansibleOptionLink" href="#parameter-cluster" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Restrict results by specific cluster.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-hub_kubeconfig"></div>
                    <b>hub_kubeconfig</b>
                    <a class="ansibleOptionLink" href="#parameter-hub_kubeconfig" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.</div>
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

    
    - name: "Retrieve information for all managed clusters"
      stolostron.core.managedcluster_info:
        hub_kubeconfig: /path/to/hub/kubeconfig

    - name: "Retrieve information for specific managed cluster"
      stolostron.core.managedcluster_info:
        hub_kubeconfig: /path/to/hub/kubeconfig
        cluster: cluster_name




.. Facts


.. Return values

Return Values
-------------
Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="2">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
                    <tr>
                                <td colspan="2">
                    <div class="ansibleOptionAnchor" id="return-results"></div>
                    <b>results</b>
                    <a class="ansibleOptionLink" href="#return-results" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>A dictionary of results output</div>
                                        <br/>
                                    </td>
            </tr>
                                        <tr>
                                    <td class="elbow-placeholder">&nbsp;</td>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-results/claims"></div>
                    <b>claims</b>
                    <a class="ansibleOptionLink" href="#return-results/claims" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>The cluster claims</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                    <td class="elbow-placeholder">&nbsp;</td>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-results/conditions"></div>
                    <b>conditions</b>
                    <a class="ansibleOptionLink" href="#return-results/conditions" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">list</span>
                       / <span style="color: purple">elements=string</span>                    </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>Conditions state of the cluster</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                    <td class="elbow-placeholder">&nbsp;</td>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-results/labels"></div>
                    <b>labels</b>
                    <a class="ansibleOptionLink" href="#return-results/labels" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">dictionary</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>Dict of cluster labels</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                    <td class="elbow-placeholder">&nbsp;</td>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-results/name"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#return-results/name" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>Managed cluster name</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                    <td class="elbow-placeholder">&nbsp;</td>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-results/version"></div>
                    <b>version</b>
                    <a class="ansibleOptionLink" href="#return-results/version" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>Version of the cluster</div>
                                        <br/>
                                    </td>
            </tr>
                    
                        </table>
    <br/><br/>

..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Maxim Babushkin (@MaxBab)



.. Parsing errors

