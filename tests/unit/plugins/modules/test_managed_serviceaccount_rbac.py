from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest

import string
import random
from unittest.mock import MagicMock
from pathlib import Path

import ansible_collections.stolostron.core.plugins.modules.managed_serviceaccount_rbac as msa_rbac


class TestGetRBACTemplateFilepaths(unittest.TestCase):
    def setUp(self):
        self.test_fixture_dir = f"{Path(__file__).resolve().parent}/fixtures/rbac_template"

    def test_empty_input(self):
        module = MagicMock()
        msa_rbac.get_rbac_template_filepaths(module, None)
        module.fail_json.assert_called()

    def test_file_not_exist(self):
        module = MagicMock()
        random_name = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        msa_rbac.get_rbac_template_filepaths(module, random_name)
        module.fail_json.assert_called()

    def test_empty_file(self):
        module = MagicMock()
        rbac_template = f"{self.test_fixture_dir}/empty_file.yml"
        result = msa_rbac.get_rbac_template_filepaths(module, rbac_template)
        module.fail_json.assert_not_called()
        assert result == [rbac_template]

    def test_empty_dir(self):
        module = MagicMock()
        rbac_template = f"{self.test_fixture_dir}/empty_dir"
        msa_rbac.get_rbac_template_filepaths(module, rbac_template)
        module.fail_json.assert_called()

    def test_non_empty_dir(self):
        module = MagicMock()
        rbac_template = f"{self.test_fixture_dir}"
        result = msa_rbac.get_rbac_template_filepaths(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 6


class TestGetYamlResourceFromFiles(unittest.TestCase):
    def setUp(self):
        self.test_fixture_dir = f"{Path(__file__).resolve().parent}/fixtures/rbac_template"

    def test_empty_input(self):
        module = MagicMock()
        msa_rbac.get_yaml_resource_from_files(module, None)
        module.fail_json.assert_called()

    def test_empty_list(self):
        module = MagicMock()
        files = []
        msa_rbac.get_yaml_resource_from_files(module, files)
        module.fail_json.assert_called()

    def test_empty_file(self):
        module = MagicMock()
        files = [f"{self.test_fixture_dir}/empty_file.yml"]
        msa_rbac.get_yaml_resource_from_files(module, files)
        module.fail_json.assert_called()

    def test_single_object_file(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/single_object_file.yml"]
        result = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 1

    def test_multi_object_file(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/five_object_file.yml"]
        result = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 5

    def test_multi_files(self):
        module = MagicMock()
        rbac_template = [
            f"{self.test_fixture_dir}/single_object_file.yml",
            f"{self.test_fixture_dir}/five_object_file.yml",
        ]
        result = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 6

    def test_non_kube_resource_file(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/lorem_ipsum.txt"]
        result = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 1

    def test_mixed_resource_files(self):
        module = MagicMock()
        rbac_template = [
            f"{self.test_fixture_dir}/lorem_ipsum.txt",
            f"{self.test_fixture_dir}/single_object_file.yml",
            f"{self.test_fixture_dir}/five_object_file.yml",
        ]
        result = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        module.fail_json.assert_not_called()
        assert len(result) == 7


class TestGetRbacResourceFromYaml(unittest.TestCase):
    def setUp(self) -> None:
        self.test_fixture_dir = f"{Path(__file__).resolve().parent}/fixtures/rbac_template"

    def test_non_kube_yaml(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/lorem_ipsum.txt"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.warn.assert_called()
        module.fail_json.assert_called()

    def test_non_rbac_yaml(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/non_rbac_resource.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.warn.assert_called()
        module.fail_json.assert_called()

    def test_single_role_yaml(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/single_object_file.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        result = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.fail_json.assert_not_called()
        assert len(result.get('Role')) == 1
        assert len(result.get('RoleBinding')) == 0
        assert len(result.get('ClusterRoleBinding')) == 0
        assert len(result.get('ClusterRole')) == 0

    def test_multi_object_yaml(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/five_object_file.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        result = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.fail_json.assert_not_called()
        assert len(result.get('Role')) == 2
        assert len(result.get('RoleBinding')) == 2
        assert len(result.get('ClusterRoleBinding')) == 1
        assert len(result.get('ClusterRole')) == 0

    def test_bad_rbac_yaml(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/bad_rbac.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.warn.assert_called()
        module.fail_json.assert_called()

    def test_good_and_bad_yaml(self):
        module = MagicMock()
        rbac_template = [
            f"{self.test_fixture_dir}/bad_rbac.yml",
            f"{self.test_fixture_dir}/single_object_file.yml"
        ]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        result = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        module.warn.assert_called()
        module.fail_json.assert_not_called()
        assert len(result.get('Role')) == 1
        assert len(result.get('RoleBinding')) == 0
        assert len(result.get('ClusterRoleBinding')) == 0
        assert len(result.get('ClusterRole')) == 0


class TestGenerateRbacManifest(unittest.TestCase):
    def setUp(self) -> None:
        self.test_fixture_dir = f"{Path(__file__).resolve().parent}/fixtures/rbac_template"
        self.role_subject = {
            'kind': 'ServiceAccount',
            'name': 'foo',
            'namespace': 'bar',
        }

    def test_no_resource(self):
        module = MagicMock()
        rbac_resources = {'Role': {}, 'ClusterRole': {}, 'RoleBinding': {}, 'ClusterRoleBinding': {}}
        msa_rbac.generate_rbac_manifest(module, rbac_resources, 'postfix', self.role_subject)
        module.fail_json.assert_called()

    def test_single_unused_role(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/single_object_file.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        rbac_resources = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        result = msa_rbac.generate_rbac_manifest(module, rbac_resources, 'postfix', self.role_subject)
        module.warn.assert_called()
        module.fail_json.assert_not_called()
        assert len(result) == 1

    def test_no_unused_role(self):
        module = MagicMock()
        rbac_template = [f"{self.test_fixture_dir}/five_object_file.yml"]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        rbac_resources = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        result = msa_rbac.generate_rbac_manifest(module, rbac_resources, 'postfix', self.role_subject)
        module.warn.assert_not_called()
        module.fail_json.assert_not_called()
        assert len(result) == 5

    def test_unused_role(self):
        module = MagicMock()
        rbac_template = [
            f"{self.test_fixture_dir}/five_object_file.yml",
            f"{self.test_fixture_dir}/single_object_file.yml",
        ]
        yaml = msa_rbac.get_yaml_resource_from_files(module, rbac_template)
        rbac_resources = msa_rbac.get_rbac_resource_from_yaml(module, yaml)
        result = msa_rbac.generate_rbac_manifest(module, rbac_resources, 'postfix', self.role_subject)
        module.warn.assert_called()
        module.fail_json.assert_not_called()
        assert len(result) == 6
