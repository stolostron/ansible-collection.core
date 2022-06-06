from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest.mock import MagicMock
from ansible_collections.stolostron.core.plugins.module_utils.installer_utils import (
    get_component_status,
    set_component_status
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
