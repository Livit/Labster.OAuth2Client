"""
Test logging provided by the LoggingBaseCommand
"""
import logging

from testfixtures import LogCapture

from oauth2_client.utils.django.base_cmd import LoggingBaseCommand
from test_case import StandaloneAppTestCase


class TestedCommand(LoggingBaseCommand):
    """
    Object Under Test
    """
    def handle(self, *args, **options):
        self.logger.debug("I am a debug message")
        self.logger.info("I am an info message")
        self.logger.warning("I am a warning message")
        self.logger.error("I am an error message")


class TestLoggingCommand(StandaloneAppTestCase):
    """
    Test logging provided by the LoggingBaseCommand.
    We expect behaviour of a standard Python logger.
    """

    def setUp(self):
        self.tested_cmd = TestedCommand()

    @classmethod
    def setUpClass(cls):
        super(TestLoggingCommand, cls).setUpClass()
        # Temporarily print all log levels.
        logging.disable(logging.NOTSET)

    @classmethod
    def tearDownClass(cls):
        super(TestLoggingCommand, cls).tearDownClass()
        # Restore test logging to ERROR only. We want clean output.
        logging.disable(logging.WARNING)

    def test_verbosity_error(self):
        """
        --verbosity=0 maps to ERROR. Ensure we see expected output.
        """
        with LogCapture() as logs:
            self.tested_cmd.run_from_argv(["one", "two", "--verbosity=0"])
            self.assertIn("I am an error message", str(logs))
            self.assertNotIn("I am a warning message", str(logs))
            self.assertNotIn("I am an info message", str(logs))
            self.assertNotIn("I am a debug message", str(logs))

    def test_verbosity_warning(self):
        """
        --verbosity=1 maps to WARNING. Ensure we see expected output.
        """
        with LogCapture() as logs:
            self.tested_cmd.run_from_argv(["one", "two", "--verbosity=1"])
            self.assertIn("I am an error message", str(logs))
            self.assertIn("I am a warning message", str(logs))
            self.assertNotIn("I am an info message", str(logs))
            self.assertNotIn("I am a debug message", str(logs))

    def test_verbosity_info(self):
        """
        --verbosity=2 maps to INFO. Ensure we see expected output.
        """
        with LogCapture() as logs:
            self.tested_cmd.run_from_argv(["one", "two", "--verbosity=2"])
            self.assertIn("I am an error message", str(logs))
            self.assertIn("I am a warning message", str(logs))
            self.assertIn("I am an info message", str(logs))
            self.assertNotIn("I am a debug message", str(logs))

    def test_verbosity_debug(self):
        """
        --verbosity=3 maps to DEBUG. Ensure we see expected output.
        """
        with LogCapture() as logs:
            self.tested_cmd.run_from_argv(["one", "two", "--verbosity=3"])
            self.assertIn("I am an error message", str(logs))
            self.assertIn("I am a warning message", str(logs))
            self.assertIn("I am an info message", str(logs))
            self.assertIn("I am a debug message", str(logs))
