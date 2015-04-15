"""Tests runner for modoboa_admin."""

import unittest

from modoboa.lib.test_utils import TestRunnerMixin


class TestRunner(TestRunnerMixin, unittest.TestCase):

    """The tests runner."""

    extension = "modoboa_postfix_autoreply"
    dependencies = [
        "modoboa_admin",
        "modoboa_admin_limits",
    ]
