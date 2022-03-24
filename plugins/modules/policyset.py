#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


DOCUMENTATION = r'''

module: policyset

short_description: Create/Update/Delete PolicySet, Policies, PlacementRule, and PlacementBinding

author:
- "Hao Liu (@TheRealHaoLiu)"
- "Hanqiu Zhang (@hanqiuzh)"
- "Nathan Weatherly (@nathanweatherly)"
- "Tsu Phin Hee (@tphee)"

description:
- Generate Open Cluster Management policies from existing Kubernetes manifests in your manifest directory.
  A policySet, placementRule, and placementBinding will be created. All policies will be group into the policySet.
- Any add/update/delete files in manifest directory, polcies will be added/updated/deleted
- Any update to the cluster_selectors, placementRule will be updated

options:
    hub_kubeconfig:
        description: Path to the Hub cluster kubeconfig. Can also be specified via K8S_AUTH_KUBECONFIG environment variable.
        type: path
        required: True
    state:
        description:
        - Determines if policySet, policies, placementRule, and placementBinding should be created, or deleted.
          When set to C(present), a policySet, policies, placementRule, and placementBinding will be created.
          If set to C(absent), an existing policySet, policies, placementRule, and placementBinding will be deleted.
        type: str
        default: present
        choices: [ absent, present ]
        required: False
    description:
        description: The description of the policySet
        type: str
        required: False
    namespace:
        description: The name of the namespace.  All resources will be created in this namespace.
        type: str
        required: True
    manifest_dir:
        description:
        - Path to the manifest directory must contain 'enforce' and 'inform' sub-directory,
          The 'enforce' and 'inform' sub-directory both must contain 'musthave', 'mustnothave', and 'mustonlyhave'
          sub-directory. The 'musthave', 'mustnothave', and 'mustonlyhave' sub-directory could contain manifest yaml
          files or other sub-directory that contains manifest yaml files. manifest_dir path will be the policySet name.
        - The path specified should either be the absolute or relative to the location of the playbook.
        - In order to avoid potential resource name collision, the name is prefix with policySet name and suffix with
          the yaml filename.
        type: path
        required: True
    github_repository_url:
        description:
        - The URL of repository on GitHub where manifest yaml files are stored.
        type: str
        required: False
    github_repository_branch:
        description:
        - The branch of repository on GitHub.
        type: str
        required: False
    github_token:
        description:
        - The access token of private repository on GitHub.
        - This is not required for public repository on GitHub.
        type: str
        required: False
    cluster_selectors:
        description:
        - Expressions to match your desired managed clusters.
          A placementRule will be created with this cluster selectors expressions.
        type: list
        required: True
    max_policy_worker_threads:
        description:
        - The maximum number of policy worker threads to do multi-thread processing
        type: int
        default: 5
        required: False

'''

EXAMPLES = r'''
- name: "Creating a PolicySet"
  ocmplus.cm.pollicyset:
    hub_kubeconfig: /path/to/hub/kubeconfig
    namespace: default
    manifest_dir: /path/to/manifest_dir
    cluster_selectors:
      - vendor=OpenShift
      - name!=local-cluster
'''

RETURN = r'''
result:
    description: message describing the policySet, policies, placementRule, and placementBinding successfully done.
    returned: success
    type: str
err:
  description: Error message
  returned: when there's an error
  type: str
  sample: null
'''

import os
import re
import tempfile
import shutil
import queue as queue
from threading import Thread
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
try:
    from ansible_collections.kubernetes.core.plugins.module_utils.apply import (
        recursive_diff,
    )
except ImportError:
    from ansible.module_utils.common.dict_transformations import recursive_diff

IMP_ERR = {}
try:
    import yaml
except ImportError as e:
    IMP_ERR['yaml'] = {'error': traceback.format_exc(),
                       'exception': e}
try:
    from jinja2 import Template
except ImportError as e:
    IMP_ERR['jinja2'] = {'error': traceback.format_exc(),
                         'exception': e}
try:
    import kubernetes
    from kubernetes.dynamic.exceptions import NotFoundError, DynamicApiError
except ImportError as e:
    IMP_ERR['k8s'] = {'error': traceback.format_exc(),
                      'exception': e}
try:
    from git import Repo
except ImportError as e:
    IMP_ERR['git'] = {'error': traceback.format_exc(),
                      'exception': e}


LABEL_KEY = 'ocmplus.cm.policyset/created'
LABEL = {LABEL_KEY: 'true'}

PLACEMENT_RULE_TEMPLATE = """
apiVersion: apps.open-cluster-management.io/v1
kind: PlacementRule
metadata:
  name: {{ name }}
  namespace: {{ namespace }}
  labels: {{ label }}
spec:
  clusterSelector:
    matchExpressions: {{ expressions }}
"""

POLICYSET_TEMPLATE = """
apiVersion: policy.open-cluster-management.io/v1beta1
kind: PolicySet
metadata:
  name: {{ name }}
  namespace: {{ namespace }}
  labels: {{ label }}
spec:
  description: {{ description }}
  policies: {{ policy_names }}
"""

POLICYSET_PLACEMENT_BINDING_TEMPLATE = """
apiVersion: policy.open-cluster-management.io/v1
kind: PlacementBinding
metadata:
  name: {{ name }}
  namespace: {{ namespace }}
  labels: {{ label }}
placementRef:
  apiGroup: apps.open-cluster-management.io
  kind: PlacementRule
  name: {{ name }}
subjects:
  - apiGroup: policy.open-cluster-management.io
    kind: PolicySet
    name: {{ name }}
"""


def render_policy(
    name,
    namespace,
    categories,
    controls,
    standards,
    remediation_action,
    severity,
    object_templates
):
    policy_template = {
        'apiVersion': 'policy.open-cluster-management.io/v1',
        'kind': 'Policy',
        'metadata': {
            'name': name,
            'namespace': namespace,
            'labels': LABEL,
            'annotations': {
                'policy.open-cluster-management.io/categories': categories,
                'policy.open-cluster-management.io/controls': controls,
                'policy.open-cluster-management.io/standards': standards,
            }
        },
        'spec': {
            'remediationAction': remediation_action,
            'disabled': False,
            'policy-templates': [
                {'objectDefinition': {
                    'apiVersion': 'policy.open-cluster-management.io/v1',
                    'kind': 'ConfigurationPolicy',
                    'metadata': {
                            'name': name
                    },
                    'spec': {
                        'remediationAction': remediation_action,
                        'severity': severity,
                        'namespaceSelector': {
                            'exclude': [
                                'kube-*'
                            ],
                            'include': [
                                namespace
                            ]
                        },
                        'object-templates': object_templates
                    }
                }
                }
            ]
        }
    }

    return policy_template


def get_filepath(module: AnsibleModule, policyset_name, manifest_dir):
    if not (os.path.exists(manifest_dir) and os.path.isdir(manifest_dir)):
        module.fail_json(
            msg=f'Error accessing {manifest_dir}. Does the directory exist?')

    remediation_actions = {'inform': 'inform', 'enforce': 'enforce'}
    compliance_types = {'musthave': 'musthave',
                        'mustonlyhave': 'mustonlyhave', 'mustnothave': 'mustnothave'}
    filenames = []
    filepaths = []
    maxlen = 253
    for subdir, dirs, files in os.walk(manifest_dir, followlinks=True):
        for file in files:
            filepath = os.path.join(subdir, file)
            for remediation_action in remediation_actions:
                for compliance_type in compliance_types:
                    if filepath.startswith(f'{manifest_dir}/{remediation_action}/{compliance_type}/') and filepath.endswith((".yml", ".yaml")):
                        # get filename without the extension
                        if filepath.endswith('.yaml'):
                            filename = filepath[:filepath.find('.yaml')]
                        else:
                            filename = filepath[:filepath.find('.yml')]
                        # get filename from last '/'
                        filename = filename.rsplit('/', 1)[-1]
                        # remove special characters
                        filename = re.sub('[^A-Za-z0-9-]+', '', filename)
                        # check if filename is already being used
                        if filename in filenames:
                            module.fail_json(
                                msg=f'Filename: {filename} already being used!'
                            )
                        # check the filename length
                        if len(f'{policyset_name}-{filename}') > maxlen:
                            module.fail_json(
                                msg=f'Filename: {filename} can contain at most {maxlen - len(policyset_name) - 1} characters'
                            )
                        filenames.append(filename)
                        item = {'filename': filename, 'remediation_action': remediation_action,
                                'compliance_type': compliance_type, 'filepath': filepath}
                        # append to the list
                        filepaths.append(item)

    if len(filepaths) == 0:
        module.fail_json(
            msg=f'No manifest file in directory: {manifest_dir}'
        )
    return filepaths


def get_policy_attributes(filepath):
    policy_attributes = {
        'policy_categories': '',
        'policy_controls': '',
        'policy_standards': '',
        'policy_severity': ''
    }
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('#'):
                for attribute in policy_attributes:
                    if line.find(attribute) != -1:
                        x = ''
                        if line.find('=') != -1:
                            x = line[line.find('=') + 1:]
                        elif line.find(':') != -1:
                            x = line[line.find(':') + 1:]
                        policy_attributes[attribute] = x.replace(
                            "'", "").replace('"', '').strip()

    return policy_attributes


def generate_object_templates(module: AnsibleModule, compliance_type, filepath):
    object_templates = []
    try:
        with open(filepath, 'r') as file:
            docs = yaml.safe_load_all(file)
            for doc in docs:
                object_templates.append(
                    {"complianceType": compliance_type, "objectDefinition": doc})
    except Exception as e:
        module.fail_json(
            msg=f"Error loading resourc file {filepath}", err=e)

    return object_templates


def ensure_policy(
    module: AnsibleModule,
    hub_client,
    name,
    namespace,
    remediation_action,
    compliance_type,
    filepath,
):
    policy_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1',
        kind='Policy',
    )
    filepath = os.path.realpath(filepath)
    object_templates = generate_object_templates(
        module, compliance_type, filepath)
    if object_templates:
        try:
            object_templates = sorted(object_templates, key=lambda s: (
                s['objectDefinition']['metadata']['name']))
        except KeyError:
            pass
    policy_attributes = get_policy_attributes(filepath)
    severities = ['low', 'Low', 'medium', 'Medium',
                  'high', 'High', 'critical', 'Critical']
    if not (policy_attributes['policy_severity'] and policy_attributes['policy_severity'] in severities):
        policy_attributes['policy_severity'] = 'low'
    try:
        policy = policy_api.get(name=name, namespace=namespace).to_dict()

        # check if Policy needs update
        update_required = False
        patch_body = render_policy(
            name,
            namespace,
            policy_attributes['policy_categories'],
            policy_attributes['policy_controls'],
            policy_attributes['policy_standards'],
            remediation_action,
            policy_attributes['policy_severity'],
            object_templates
        )
        diff = recursive_diff(policy, patch_body)
        if diff and len(diff) > 1 and diff[1]:
            if diff[1].get('metadata') or diff[1].get('spec'):
                update_required = True

            if update_required:
                # patch Policy
                try:
                    policy_api.patch(
                        name=name,
                        namespace=namespace,
                        body=diff[1],
                        content_type="application/merge-patch+json"
                    )
                except DynamicApiError as e:
                    module.fail_json(
                        msg=f'Failed to patch Policy: {name} namespace: {namespace}.', err=e)
    except NotFoundError:
        policy_yaml = render_policy(
            name,
            namespace,
            policy_attributes['policy_categories'],
            policy_attributes['policy_controls'],
            policy_attributes['policy_standards'],
            remediation_action,
            policy_attributes['policy_severity'],
            object_templates
        )
        policy = policy_api.create(policy_yaml)

    return policy


def generate_expression(cluster_selectors):
    operators = {
        '!=': 'NotIn',
        '=': 'In'
    }
    expressions = []
    for selector in cluster_selectors:
        for key, value in operators.items():
            x = selector.split(key)
            if len(x) == 2:
                values = x[1].split(",")
                values = list(map(str.strip, values))
                expression = {
                    'key': x[0].strip(), 'operator': value, 'values': values}
                break
            else:
                expression = {'key': selector.strip(), 'operator': 'Exists'}
        expressions.append(expression)

    return expressions


class Policy(Thread):
    def __init__(
        self,
        in_queue,
        out_queue,
        module,
        hub_client,
        namespace
    ):
        Thread.__init__(self)
        self.in_queue = in_queue
        self.out_queue = out_queue
        self.module = module
        self.hub_client = hub_client
        self.namespace = namespace

    def run(self):
        while True:
            # Grabs item from queue
            item = self.in_queue.get()
            try:
                policy = ensure_policy(
                    self.module,
                    self.hub_client,
                    item['policy_name'],
                    self.namespace,
                    item['remediation_action'],
                    item['compliance_type'],
                    item['filepath']
                )

                self.out_queue.put(policy['metadata']['name'])
            except Exception as e:
                self.module.warning(
                    msg=f"Failed to ensure Policy: {item['policy_name']} namespace: {self.namespace}.", err=e)
            finally:
                # Signals to queue job is done
                self.in_queue.task_done()


def ensure_all_policies(
        max_policy_worker_threads,
        module,
        hub_client,
        namespace,
        manifest_dir,
        policyset_name
):
    in_queue = queue.Queue()
    out_queue = queue.Queue()

    # Spawn a pool of threads, and pass them queue instance
    for i in range(max_policy_worker_threads):
        t = Policy(
            in_queue,
            out_queue,
            module,
            hub_client,
            namespace
        )
        t.daemon = True
        t.start()

    for item in get_filepath(module, policyset_name, manifest_dir):
        in_queue.put({
            'policy_name': f'{policyset_name}-{item["filename"]}',
            'remediation_action': item['remediation_action'],
            'compliance_type': item['compliance_type'],
            'filepath': item.get('filepath')
        })

    # Wait on the queue until everything has been processed
    in_queue.join()
    policy_names = []
    while True:
        if not out_queue.empty():
            policy_names.append(out_queue.get())
        else:
            break

    return policy_names


def ensure_placement(module: AnsibleModule, hub_client, name, namespace, cluster_selectors):
    placement_api = hub_client.resources.get(
        api_version='apps.open-cluster-management.io/v1',
        kind='PlacementRule',
    )
    expressions = generate_expression(cluster_selectors)
    try:
        placement = placement_api.get(name=name, namespace=namespace).to_dict()

        # check if PlacementRule needs update
        old_expressions = placement['spec']['clusterSelector'].get(
            'matchExpressions')
        if old_expressions:
            old_expressions = sorted(old_expressions, key=lambda s: s['key'])
        if expressions:
            expressions = sorted(expressions, key=lambda s: s['key'])
        if not (expressions == old_expressions):
            # patch PlacementRule expressions
            patch_body = {
                "spec": {
                    "clusterSelector": {
                        "matchExpressions": expressions
                    }
                }
            }

            try:
                placement_api.patch(name=name, namespace=namespace, body=patch_body,
                                    content_type="application/merge-patch+json")
            except DynamicApiError as e:
                module.fail_json(
                    msg=f'Failed to patch PlacementRule: {name} namespace: {namespace}.', err=e)
    except NotFoundError:
        render_config = {
            'label': LABEL,
            'name': name,
            'namespace': namespace,
            'expressions': expressions
        }
        new_placement_raw = Template(PLACEMENT_RULE_TEMPLATE).render(
            render_config
        )
        placement_yaml = yaml.safe_load(
            new_placement_raw)
        placement = placement_api.create(
            placement_yaml)

    return placement


def ensure_placement_binding(module: AnsibleModule, hub_client, name, namespace):
    placement_binding_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1',
        kind='PlacementBinding',
    )
    try:
        placement_binding = placement_binding_api.get(
            name=name, namespace=namespace)
    except NotFoundError:
        render_config = {
            'label': LABEL,
            'name': name,
            'namespace': namespace
        }
        new_placement_binding_raw = Template(POLICYSET_PLACEMENT_BINDING_TEMPLATE).render(
            render_config
        )
        placement_binding_yaml = yaml.safe_load(
            new_placement_binding_raw)
        placement_binding = placement_binding_api.create(
            placement_binding_yaml)

    return placement_binding


def render_policyset(name, description, namespace, policy_names):
    render_config = {
        'label': LABEL,
        'name': name,
        'description': description,
        'namespace': namespace,
        'policy_names': policy_names
    }
    new_policyset_raw = Template(POLICYSET_TEMPLATE).render(
        render_config
    )
    return yaml.safe_load(new_policyset_raw)


def ensure_policyset(module: AnsibleModule, hub_client, name, description, namespace, policy_names):
    policyset_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1beta1',
        kind='PolicySet',
    )
    if description is None:
        description = ''
    try:
        policyset = policyset_api.get(name=name, namespace=namespace)

        # check if PolicySet needs update
        old_policies = policyset.spec.get('policies')
        added_policies = set(policy_names) - set(old_policies)
        deleted_policies = set(old_policies) - set(policy_names)
        # delete policies that got removed from manifest_dir
        for policy in deleted_policies:
            delete_policy(module, hub_client, policy, namespace)

        update_required = False
        patch_body = {'spec': {}}
        if added_policies or deleted_policies:
            # patch policy list
            patch_body['spec']['policies'] = policy_names
            update_required = True

        if description != policyset.spec.get('description', ''):
            # patch description
            patch_body['spec']['description'] = description
            update_required = True

        if update_required:
            try:
                policyset_api.patch(name=name, namespace=namespace, body=patch_body,
                                    content_type="application/merge-patch+json")
            except DynamicApiError as e:
                module.fail_json(
                    msg=f'Failed to patch PolicySet: {name} namespace: {namespace}.', err=e)
    except NotFoundError:
        policyset_yaml = render_policyset(
            name,
            description,
            namespace,
            policy_names
        )
        policyset = policyset_api.create(policyset_yaml)

    return policyset


def delete_placement_rule(module: AnsibleModule, hub_client, name, namespace):
    placement_rule_api = hub_client.resources.get(
        api_version='apps.open-cluster-management.io/v1',
        kind='PlacementRule',
    )

    try:
        placement_rule = placement_rule_api.get(name=name, namespace=namespace)
    except NotFoundError:
        return False

    # check if this was created by this plugin
    if placement_rule.metadata.get('labels') and placement_rule.metadata.labels.get(LABEL_KEY):
        status = placement_rule_api.delete(name=name, namespace=namespace)
        return (status.status == 'Success')

    return False


def delete_placement_binding(module: AnsibleModule, hub_client, name, namespace):
    placement_binding_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1',
        kind='PlacementBinding',
    )

    try:
        placement_binding = placement_binding_api.get(
            name=name, namespace=namespace)
    except NotFoundError:
        return False

    # check if this was created by this plugin
    if placement_binding.metadata.get('labels') and placement_binding.metadata.labels.get(LABEL_KEY):
        status = placement_binding_api.delete(name=name, namespace=namespace)
        return (status.status == 'Success')

    return False


def delete_policy(module: AnsibleModule, hub_client, name, namespace):
    policy_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1',
        kind='Policy',
    )

    try:
        policy = policy_api.get(name=name, namespace=namespace)
    except NotFoundError:
        return False

    # check if this was created by this plugin
    if policy.metadata.get('labels') and policy.metadata.labels.get(LABEL_KEY):
        status = policy_api.delete(name=name, namespace=namespace)
        return (status.status == 'Success')

    return False


class Delete_policy(Thread):
    def __init__(
        self,
        in_queue,
        module,
        hub_client,
        namespace
    ):
        Thread.__init__(self)
        self.in_queue = in_queue
        self.module = module
        self.hub_client = hub_client
        self.namespace = namespace

    def run(self):
        while True:
            # Grabs item from queue
            policy_name = self.in_queue.get()
            try:
                delete_policy(self.module, self.hub_client,
                              policy_name, self.namespace)
            except Exception as e:
                self.module.warning(
                    msg=f"Failed to delete Policy: {policy_name} namespace: {self.namespace}.", err=e)
            finally:
                # Signals to queue job is done
                self.in_queue.task_done()


def delete_all_policies(
        module,
        max_policy_worker_threads,
        hub_client,
        namespace,
        policies
):
    in_queue = queue.Queue()

    # Spawn a pool of threads, and pass them queue instance
    for i in range(max_policy_worker_threads):
        t = Delete_policy(
            in_queue,
            module,
            hub_client,
            namespace
        )
        t.daemon = True
        t.start()

    for policy_name in policies:
        in_queue.put(policy_name)

    # Wait on the queue until everything has been processed
    in_queue.join()


def delete_policyset(module: AnsibleModule, hub_client, name, namespace):
    policyset_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1beta1',
        kind='PolicySet',
    )

    try:
        policyset_api.get(name=name, namespace=namespace)
    except NotFoundError:
        return True

    status = policyset_api.delete(name=name, namespace=namespace)

    return (status.status == 'Success')


def delete_all(module: AnsibleModule, max_policy_worker_threads, hub_client, name, namespace):
    policyset_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1beta1',
        kind='PolicySet',
    )

    try:
        policyset = policyset_api.get(name=name, namespace=namespace)
    except NotFoundError:
        return None

    delete_all_policies(
        module,
        max_policy_worker_threads,
        hub_client,
        namespace,
        policyset.spec.get('policies')
    )

    placements = policyset.status.get('placement')
    for placement in placements:
        placement_rule = placement.get('placementRule')
        delete_placement_rule(module, hub_client, placement_rule, namespace)
        placement_binding = placement.get('placementBinding')
        delete_placement_binding(
            module, hub_client, placement_binding, namespace)

    return delete_policyset(module, hub_client, name, namespace)


def clone_repo(module: AnsibleModule, github_repo_url, github_repo_branch, github_token):
    if github_token:
        pos = github_repo_url.find("//")
        if pos > 0:
            github_repo_url = f"{github_repo_url[:pos+2]}{github_token}@{github_repo_url[pos+2:]}"
        else:
            module.fail_json(
                msg=f'invalid github_repo_url {github_repo_url}')

    repo_path = tempfile.mkdtemp()
    try:
        repository = Repo.clone_from(github_repo_url, repo_path)

        if github_repo_branch:
            repository.git.checkout(github_repo_branch)
    except Exception as e:
        shutil.rmtree(repo_path)
        module.fail_json(
            msg=f'failed to clone repo {github_repo_url}', err=e)

    return repo_path


def validates(module: AnsibleModule, hub_client, namespace, policyset_name):
    namespace_api = hub_client.resources.get(
        api_version='v1',
        kind='Namespace',
    )
    try:
        namespace_api.get(name=namespace)
    except NotFoundError:
        module.fail_json(
            msg=f'Does the namespace: {namespace} exist?')

    policyset_api = hub_client.resources.get(
        api_version='policy.open-cluster-management.io/v1beta1',
        kind='PolicySet',
    )

    try:
        policyset = policyset_api.get(name=policyset_name, namespace=namespace)
        # check if policyset was created by this plugin
        if policyset.metadata.get('labels') and policyset.metadata.labels.get(LABEL_KEY):
            return True
        else:
            # it was not created by this plugin
            module.fail_json(
                msg=f'PoicySet: {policyset_name} already exist but was not created by this plugin')
    except NotFoundError:
        return True

    return True


def execute_module(module: AnsibleModule):
    if 'k8s' in IMP_ERR:
        # we will need k8s for this module
        module.fail_json(msg=missing_required_lib('kubernetes'),
                         exception=IMP_ERR['k8s']['exception'])
    if 'jinja2' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('jinja2'),
                         exception=IMP_ERR['jinja2']['exception'])
    if 'yaml' in IMP_ERR:
        module.fail_json(msg=missing_required_lib('yaml'),
                         exception=IMP_ERR['yaml']['exception'])

    hub_kubeconfig = kubernetes.config.load_kube_config(
        config_file=module.params['hub_kubeconfig'])
    hub_client = kubernetes.dynamic.DynamicClient(
        kubernetes.client.api_client.ApiClient(configuration=hub_kubeconfig)
    )
    max_policy_worker_threads = module.params['max_policy_worker_threads']
    namespace = module.params['namespace']
    manifest_dir = module.params['manifest_dir']
    policyset_name = manifest_dir.rsplit('/', 1)[-1]
    # validates namespace and policyset_name
    validates(module, hub_client, namespace, policyset_name)
    # remove special characters
    policyset_name = re.sub('[^A-Za-z0-9\-]+', '', policyset_name)
    state = module.params['state']
    if state == 'present':
        description = module.params['description']
        cluster_selectors = module.params['cluster_selectors']
        github_repo_url = module.params['github_repository_url']
        github_repo_branch = module.params['github_repository_branch']
        github_token = module.params['github_token']
        repo_path = None
        if github_repo_url:
            repo_path = clone_repo(
                module, github_repo_url, github_repo_branch, github_token)
            manifest_dir = os.path.join(repo_path, manifest_dir)
        policy_names = ensure_all_policies(
            max_policy_worker_threads,
            module,
            hub_client,
            namespace,
            manifest_dir,
            policyset_name
        )
        ensure_policyset(module, hub_client, policyset_name,
                         description, namespace, policy_names)
        ensure_placement(module, hub_client, policyset_name,
                         namespace, cluster_selectors)
        ensure_placement_binding(module, hub_client, policyset_name, namespace)
        if repo_path:
            shutil.rmtree(repo_path)
    else:
        delete_all(module, max_policy_worker_threads,
                   hub_client, policyset_name, namespace)

    module.exit_json(
        result='PolicySet, Policies, PlacementRule, and PlacementBinding successfully done')


def main():
    argument_spec = dict(
        hub_kubeconfig=dict(type='path', required=True, fallback=(
            env_fallback, ['K8S_AUTH_KUBECONFIG'])),
        state=dict(
            type='str', default='present', choices=['present', 'absent']
        ),
        description=dict(type='str', required=False),
        namespace=dict(type='str', required=True),
        manifest_dir=dict(type='path', required=True),
        github_repository_url=dict(type='str', required=False),
        github_repository_branch=dict(type='str', required=False),
        github_token=dict(type='str', no_log=True, required=False),
        cluster_selectors=dict(type='list', elements='str', required=True),
        max_policy_worker_threads=dict(type='int', default=5)
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_if=[
            ('state', 'absent', ['namespace', 'manifest_dir']),
        ],
        supports_check_mode=True,
    )

    execute_module(module)


if __name__ == '__main__':
    main()
