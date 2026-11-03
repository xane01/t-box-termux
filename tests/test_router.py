"""Command-line routing regression tests."""
import unittest
from unittest.mock import patch

from core import router


class PluginInfoRoutingTests(unittest.TestCase):
    def test_plugin_info_command_reaches_package_handler(self):
        with patch.object(router, "ensure_dirs"), \
             patch.object(router, "cmd_package", return_value=0) as handler:
            result = router.main(["plugin-info", "sample-plugin"])

        self.assertEqual(result, 0)
        handler.assert_called_once()
        args = handler.call_args.args[0]
        self.assertEqual(args.package_action, "info")
        self.assertEqual(args.module_id, "sample-plugin")


if __name__ == "__main__":
    unittest.main()
