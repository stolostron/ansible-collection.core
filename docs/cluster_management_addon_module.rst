.. Document meta

:orphan:

.. Anchors

.. _ansible_collections.stolostron.core.cluster_management_addon_module:

.. Anchors: short name for ansible.builtin

.. Anchors: aliases



.. Title

stolostron.core.cluster_management_addon -- cluster management addon
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This plugin is part of the `stolostron.core collection <https://galaxy.ansible.com/stolostron/core>`_ (version 0.0.1).

    To install it use: :code:`ansible-galaxy collection install stolostron.core`.

    To use it in a playbook, specify: :code:`stolostron.core.cluster_management_addon`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Use cluster_management_addon to enable/disable a feature on the hub. Users can only install an addon on managed clusters if the feature of that addon is enabled. This plugin will need access to the Multicloudhub CR, and it enables/disables available features by updating the corresponding fields in the CR.


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
                    <div class="ansibleOptionAnchor" id="parameter-addon_name"></div>
                    <b>addon_name</b>
                    <a class="ansibleOptionLink" href="#parameter-addon_name" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                 / <span style="color: red">required</span>                    </div>
                                                        </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li>cluster-proxy</li>
                                                                                                                                                                                                <li>managed-serviceaccount</li>
                                                                                                                                                                                                <li>search-collector</li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                            <div>Name of the feature to enable/disable.</div>
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
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-state"></div>
                    <b>state</b>
                    <a class="ansibleOptionLink" href="#parameter-state" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                            <ul style="margin: 0; padding: 0"><b>Choices:</b>
                                                                                                                                                                <li>absent</li>
                                                                                                                                                                                                <li><div style="color: blue"><b>present</b>&nbsp;&larr;</div></li>
                                                                                    </ul>
                                                                            </td>
                                                                <td>
                                            <div>Determines if feature should be enabled, or disabled. When set to <code>present</code>, a feature will be enabled. If set to <code>absent</code>, an existing feature will be disabled.</div>
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
                                            <div>Number of seconds to wait for the addon to show up.</div>
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
                                            <div>Whether to wait for an addon feature to show up. This configuration will be ignored when the state is &#x27;absent&#x27;.</div>
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

    
    - name: "Enabled cluster-proxy addon"
      stolostron.core.cluster_management_addon:
        state: present
        hub_kubeconfig: /path/to/hub/kubeconfig
        addon_name: cluster-proxy

    - name: "Disabled cluster-proxy addon"
      stolostron.core.cluster_management_addon:
        state: absent
        hub_kubeconfig: /path/to/hub/kubeconfig
        addon_name: cluster-proxy




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
                <td>always</td>
                <td>
                                            <div>human readable message describing the addon is enabled/disabled.</div>
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

