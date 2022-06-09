.. Document meta

:orphan:

.. Anchors

.. _ansible_collections.stolostron.core.managed_serviceaccount_module:

.. Anchors: short name for ansible.builtin

.. Anchors: aliases



.. Title

stolostron.core.managed_serviceaccount -- managed serviceaccount
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. Collection note

.. note::
    This plugin is part of the `stolostron.core collection <https://galaxy.ansible.com/stolostron/core>`_ (version 0.0.1).

    To install it use: :code:`ansible-galaxy collection install stolostron.core`.

    To use it in a playbook, specify: :code:`stolostron.core.managed_serviceaccount`.

.. version_added


.. contents::
   :local:
   :depth: 1

.. Deprecated


Synopsis
--------

.. Description

- Use the managed-serviceaccount to setup a serviceaccount on a managedcluster, and return the serviceaccount token.


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
                    <div class="ansibleOptionAnchor" id="parameter-generate_name"></div>
                    <b>generate_name</b>
                    <a class="ansibleOptionLink" href="#parameter-generate_name" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>This field is a prefix used to generate a unique name if the name field has not been provided.</div>
                                            <div>If this field is used the value will be combined with a unique suffix.</div>
                                            <div>The provided value has the same validation rules as the name field and may truncate by the length of the suffix required to make the value unique.</div>
                                            <div>Consider using this field with ttl_seconds_after_creation to avoid accumulation of managed-serviceaccount objects.</div>
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
                                            <div>Name of managed cluster to create serviceaccount.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-name"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#parameter-name" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">string</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>This field specify the name of managed-serviceaccount.</div>
                                            <div>The name must be unique for a specific managed-cluster.</div>
                                            <div>Use this field for persistent and long lived managed-serviceaccount.</div>
                                            <div>Consider using generate_name if the managed-serviceaccount is temporary to avoid collision between playbooks.</div>
                                            <div>Required if <code>state=absent</code></div>
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
                                            <div>Determines if managed-serviceaccount should be created, or deleted. When set to <code>present</code>, an object will be created. If set to <code>absent</code>, an existing object will be deleted.</div>
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
                                            <div>Number of seconds to wait for the managed-serviceaccount to show up.</div>
                                                        </td>
            </tr>
                                <tr>
                                                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="parameter-ttl_seconds_after_creation"></div>
                    <b>ttl_seconds_after_creation</b>
                    <a class="ansibleOptionLink" href="#parameter-ttl_seconds_after_creation" title="Permalink to this option"></a>
                    <div style="font-size: small">
                        <span style="color: purple">integer</span>
                                                                    </div>
                                                        </td>
                                <td>
                                                                                                                                                            </td>
                                                                <td>
                                            <div>The lifetime of a ManagedServiceAccount in seconds. If set, the ManagedServiceAccount will be automatically deleted. If this field is unset, the ManagedServiceAccount won&#x27;t be automatically deleted. If this field is set to zero, the ManagedServiceAccount will be deleted immediately after it creation.</div>
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
                                            <div>Whether to wait for managed-serviceaccount to show up.</div>
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

    
    - name: "Get serviceaccount token"
      stolostron.core.managed_serviceaccount:
        hub_kubeconfig: /path/to/hub/kubeconfig
        managed_cluster: example-cluster
        wait: True
        timeout: 60
      register: managed_serviceaccount

    - name: "Remove an existing managed-serviceaccount object"
      stolostron.core.managed_serviceaccount:
        state: absent
        hub_kubeconfig: /path/to/hub/kubeconfig
        managed_cluster: example-cluster
        name: managed-serviceaccount-name
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
                    <div class="ansibleOptionAnchor" id="return-managed_cluster"></div>
                    <b>managed_cluster</b>
                    <a class="ansibleOptionLink" href="#return-managed_cluster" title="Permalink to this return value"></a>
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
                                            <div>human readable message describing the managed serviceaccount is ready or not.</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-name"></div>
                    <b>name</b>
                    <a class="ansibleOptionLink" href="#return-name" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>Managed ServiceAccount name</div>
                                        <br/>
                                    </td>
            </tr>
                                <tr>
                                <td colspan="1">
                    <div class="ansibleOptionAnchor" id="return-token"></div>
                    <b>token</b>
                    <a class="ansibleOptionLink" href="#return-token" title="Permalink to this return value"></a>
                    <div style="font-size: small">
                      <span style="color: purple">string</span>
                                          </div>
                                    </td>
                <td>success</td>
                <td>
                                            <div>ServiceAccount token</div>
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

