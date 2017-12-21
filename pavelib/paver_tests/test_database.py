"""
Tests for the Paver commands for updating test databases
"""
import os
from unittest import TestCase

import boto
from mock import patch

from common.test.utils import MockS3Mixin
from pavelib.database import verify_fingerprint_in_bucket


class TestPaverDatabaseTasks(MockS3Mixin, TestCase):
    """Tests for the Database cache file manipulation."""
    def setUp(self):
        super(TestPaverDatabaseTasks, self).setUp()
        self.conn = boto.connect_s3()
        self.conn.create_bucket('moto_test_bucket')
        self.bucket = self.conn.get_bucket('moto_test_bucket')

    @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    def test_fingerprint_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
        key.set_contents_from_string('this is a test')
        self.assertTrue(verify_fingerprint_in_bucket('testfile'))

    @patch.dict(os.environ, {'DB_CACHE_S3_BUCKET': 'moto_test_bucket'})
    def test_fingerprint_not_in_bucket(self):
        key = boto.s3.key.Key(bucket=self.bucket, name='testfile.zip')
        key.set_contents_from_string('this is a test')
        self.assertFalse(verify_fingerprint_in_bucket('otherfile'))
