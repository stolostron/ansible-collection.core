.. Document meta

:orphan:

.. Anchors

.. _ansible_collections.stolostron.core.managed_serviceaccount_rbac_module:

.. Anchors: short name for ansible.builtin

.. Anchors: aliases



.. Title

stolostron.core.managed_serviceaccount_rbac -- managed-serviceaccount RBAC
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This plugin is part of the `stolostron.core collection <https://galaxy.ansible.com/stolostron/core>`_ (version 0.0.1).

    To install it use: :code:`ansible-galaxy collection install stolostron.core`.

    To use it in a playbook, specify: :code:`stolostron.core.managed_serviceaccount_rbac`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Use the managed-serviceaccount RBAC to setup a serviceaccount on a managedcluster with the specified RBAC permission.


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
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-managed_cluster"></div>
                    <b>managed_cluster</b>
                    <a class="ansibleOptionLink" href="#parameter-managed_cluster" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of the managed cluster.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-managed_serviceaccount_name"></div>
                    <b>managed_serviceaccount_name</b>
                    <a class="ansibleOptionLink" href="#parameter-managed_serviceaccount_name" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Name of managed-serviceaccount.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-rbac_template"></div>
                    <b>rbac_template</b>
                    <a class="ansibleOptionLink" href="#parameter-rbac_template" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">path</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>Path to the file or directory that contains the role/clusterrole/rolebinding/clusterrolebinding configuration.</div>
                                            <div>The path specified should either be the absolute or relative to the location of the playbook.</div>
                                            <div>In order to avoid potential resource name collision, the last 12 digits of the target managed-serviceaccount UID will be appended to the name specified in the RBAC files.&quot;</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-timeout"></div>
                    <b>timeout</b>
                    <a class="ansibleOptionLink" href="#parameter-timeout" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                                    <b>Default:</b><br/><div style="color: blue">60</div>
                                    </td>
                                                                <td>
                                            <div>Number of seconds to wait for the resources to show up.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-wait"></div>
                    <b>wait</b>
                    <a class="ansibleOptionLink" href="#parameter-wait" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">boolean</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                                                                                    <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li><div style="color: blue"><b>no</b>&nbsp;&larr;</div></li>
                                                                                                                                                                                                <li>yes</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                            <div>Whether to wait for the resources to show up.</div>
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

    
    - name: "Configure RBAC"
      stolostron.core.managed_serviceaccount_rbac:
        hub_kubeconfig: /path/to/hub/kubeconfig
        managed_cluster: example-cluster
        managed_serviceaccount_name: managed-serviceaccount-name
        rbac_template: /path/to/rbac_template
        wait: True
        timeout: 60




.. Facts


.. Return values

Return Values
-------------
Common return values are documented :ref:`here <common_return_values>`, the following are the fields unique to this module:

.. raw:: html

    <table border=0 cellpadding=0 class="documentation-table">
        <tr>
            <th colspan="1">Key</th>
            <th>Returned</th>
            <th width="100%">Description</th>
        </tr>
                    <tr>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-exception"></div>
                    <b>exception</b>
                    <a class="ansibleOptionLink" href="#return-exception" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">complex</span>
                                          </div>
                                    </td>
                <td>when exception is catched</td>
                <td>
                                            <div>exception catched during the process.</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-msg"></div>
                    <b>msg</b>
                    <a class="ansibleOptionLink" href="#return-msg" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>message describing the RBAC configuration successfully done.</div>
                                        <br/>
                                    </td>
            </tr>
                        </table>
    <br/><br/>

..  Status (Presently only deprecated)


.. Authors

Authors
~~~~~~~

- Hao Liu (@TheRealHaoLiu)
- Hanqiu Zhang (@hanqiuzh)
- Nathan Weatherly (@nathanweatherly)
- Tsu Phin Hee (@tphee)



.. Parsing errors

