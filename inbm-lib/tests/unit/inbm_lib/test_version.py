from unittest import TestCase
from inbm_lib.version import get_inbm_version, get_inbm_commit
from inbm_lib.version import get_friendly_inbm_version_commit
from mock import patch

INBM_VERSION_TEXT = "Version: 1.2.3\r\nCommit: abcdefg\r\n"

class TestVersion(TestCase):
    @patch('inbm_lib.version._read_inbm_version_file')
    def test_get_inbm_version(self, version):
        version.return_value = INBM_VERSION_TEXT
        self.assertEquals("1.2.3", get_inbm_version())

    @patch('inbm_lib.version._read_inbm_version_file')
    def test_get_inbm_commit(self, version):
        version.return_value = INBM_VERSION_TEXT
        self.assertEquals("abcdefg", get_inbm_commit())

    @patch('inbm_lib.version._read_inbm_version_file')
    def test_get_friendly_inbm_version_commit(self, tc,):
        tc.return_value = INBM_VERSION_TEXT

        self.assertEquals("Intel(R) Manageability version 1.2.3 (abcdefg)", get_friendly_inbm_version_commit())
