from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest.mock import MagicMock
from ansible_collections.ocmplus.cm.plugins.module_utils.installer_utils import (
    get_component_status,
    get_csv_version,
    set_component_status,
    compare_version
)


class TestGetComponentStatus(unittest.TestCase):
    def test_empty_input(self):
        obj = None
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name") is False
        module.fail_json.assert_not_called()

    def test_overrides_not_exist(self):
        obj = {
            "spec": {}
        }
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name") is False
        module.fail_json.assert_not_called()

    def test_components_not_exist(self):
        obj = {
            "spec": {"overrides": {}}
        }
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name") is False
        module.fail_json.assert_not_called()

    def test_components_empty(self):
        obj = {
            "spec": {"overrides": {
                "components": []
            }}
        }
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name") is False
        module.fail_json.assert_not_called()

    def test_one_component_wrong_format(self):
        obj = {
            "spec": {"overrides": {
                "components": "wrong-format"
            }}
        }
        module = MagicMock()
        get_component_status(obj, module, "test-component-name")
        module.fail_json.assert_called()
        obj = {
            "spec": {"overrides": {
                "components": [
                    "test-component-name"
                ]
            }}
        }
        module = MagicMock()
        get_component_status(obj, module, "test-component-name")
        module.fail_json.assert_called()

    def test_component_is_enabled(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name",
                        "enabled": True,
                    }
                ]
            }}
        }
        module = MagicMock()
        assert get_component_status(obj, module, "test-component-name") is True
        module.fail_json.assert_not_called()

    def test_component_is_disabled(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name",
                        "enabled": False,
                    }
                ]
            }}
        }
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name") is False

    def test_component_is_missing(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name",
                        "enabled": False,
                    }
                ]
            }}
        }
        module = MagicMock()
        assert get_component_status(
            obj, module, "test-component-name-different") is False


class TestSetComponentStatus(unittest.TestCase):
    def test_empty_input(self):
        module = MagicMock()
        set_component_status(None, module, "test-component-name", True)
        module.fail_json.assert_called()

    def test_empty_overrides(self):
        obj = {
            "spec": {"overrides": {}}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", False)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [{
            "name": "test-component-name",
            "enabled": False
        }]

    def test_empty_components(self):
        obj = {
            "spec": {"overrides": {
                "components": []
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", False)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [{
            "name": "test-component-name",
            "enabled": False
        }]

    def test_one_component_wrong_format(self):
        obj = {
            "spec": {"overrides": {
                "components": "wrong-format"
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", False)
        module.fail_json.assert_called()
        obj = {
            "spec": {"overrides": {
                "components": [
                    "test-component-name"
                ]
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", False)
        module.fail_json.assert_called()

    def test_missing_component(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name-exist",
                        "enabled": False,
                    }
                ]
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", True)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [
            {
                "name": "test-component-name-exist",
                "enabled": False,
            },
            {
                "name": "test-component-name",
                "enabled": True
            }]

    def test_no_change_component(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name",
                        "enabled": True,
                    }
                ]
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", True)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [{
            "name": "test-component-name",
            "enabled": True
        }]

    def test_update_component(self):
        obj = {
            "spec": {"overrides": {
                "components": [
                    {
                        "name": "test-component-name",
                        "enabled": False,
                    }
                ]
            }}
        }
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", True)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [{
            "name": "test-component-name",
            "enabled": True
        }]
        module = MagicMock()
        set_component_status(obj, module, "test-component-name", False)
        module.fail_json.assert_not_called()
        assert obj["spec"]["overrides"]["components"] == [{
            "name": "test-component-name",
            "enabled": False
        }]


class TestCompareVersion(unittest.TestCase):
    def test_empty_input(self):
        assert compare_version(None, "2.3.0") is False

    def test_invalid_input(self):
        assert compare_version("abcde", "0.0.1") is False
        assert compare_version("abcde1.2.3", "0.0.1") is False

    def test_lower_version(self):
        assert compare_version("2.3.0", "2.3.1") is False
        assert compare_version("2.2.99", "2.3.0") is False
        assert compare_version("1.4.3", "2.1.1") is False

    def test_higher_equal_version(self):
        assert compare_version("2.3.1", "2.3.1") is True
        assert compare_version("2.3.2", "2.3.1") is True
        assert compare_version("2.4.0", "2.3.1") is True
        assert compare_version("3.1.0", "2.3.1") is True

    def test_partial_input(self):
        # should use 0 to fill missing parts
        assert compare_version("2", "2.0.0") is False
        assert compare_version("3", "2.1.0") is False
        assert compare_version("2.1", "2.0.1") is False
        assert compare_version("2.1", "2.1.0") is False

    def test_additional_info_ignored(self):
        # should ignore prerelease information
        assert compare_version("2.0.0-rc1", "2.0.0") is True
        assert compare_version("2.0.0", "2.0.0-rc1") is True
        assert compare_version("2.1.2-rc1", "2.1.1") is True
        assert compare_version("2.1.2-rc1", "2.1.3") is False
        assert compare_version("2.1.3-alpha1", "2.1.3-beta1") is True
        assert compare_version("2.1.2-alpha1", "2.1.3-beta1") is False
        assert compare_version("2.1.3-alpha1+abc", "2.1.3-beta1+def") is True
        assert compare_version("2.1.2-alpha1+abc", "2.1.3-beta1+def") is False


class TestGetCsvVersion(unittest.TestCase):
    def test_empty_input(self):
        assert get_csv_version(None, "") is None
        assert get_csv_version(None, "abc") is None

    def test_no_version_information(self):
        csv_no_version = {
            "spec": {},
            "metadata": {
                "name": "abc"
            }
        }
        assert get_csv_version(csv_no_version, "abc") is None

    def test_version_in_spec(self):
        csv_spec_version = {
            "spec": {"version": "1.2.3"},
            "metadata": {
                "name": "abc"
            }
        }
        assert get_csv_version(csv_spec_version, "abc") == "1.2.3"

    def test_version_in_name(self):
        csv_name_version_no_spec_version = {
            "spec": {},
            "metadata": {
                "name": "abc.v1.2.3"
            }
        }
        csv_name_version_spec_version_empty = {
            "spec": {"version": ""},
            "metadata": {
                "name": "abc.v2.4.5"
            }
        }
        assert get_csv_version(
            csv_name_version_no_spec_version, "abc") == "1.2.3"
        assert get_csv_version(
            csv_name_version_spec_version_empty, "abc") == "2.4.5"

    def test_version_in_spec_priority(self):
        csv_name_version_spec_version_priority = {
            "spec": {"version": "1.3.4"},
            "metadata": {
                "name": "abc.v2.4.5"
            }
        }
        assert get_csv_version(
            csv_name_version_spec_version_priority, "abc") == "1.3.4"
