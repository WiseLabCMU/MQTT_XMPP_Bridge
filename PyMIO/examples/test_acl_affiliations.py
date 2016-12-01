#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

################################################################################
## @package tests
#  Mortar IO (MIO) Python2 Library
#
#  Copyright (C) 2014, Carnegie Mellon University
#  All rights reserved.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 2.0 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Contributing Authors (specific to this file):
#
#  Artur Balanuta 		artur[dot]balanuta[at]tecnico[dot]pt
################################################################################

# MIO Metadata example test

import unittest
import uuid

from mio import MIO


class TestMetaData(unittest.TestCase):

	NODE_EXAMPLE = str(uuid.uuid4())

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")
		self.mio.node_create(self.NODE_EXAMPLE)

	def tearDown(self):
		self.mio.node_delete(self.NODE_EXAMPLE)
		self.mio.stop()

	def test_acl_affiliations_query(self):
		real = self.mio.acl_affiliations_query(self.NODE_EXAMPLE)
		expected = [
			{'affiliation': 'owner',
			'jid': 'testuser@sensor.andrew.cmu.edu'}]
		self.assertEqual(expected, real)

	def test_acl_affiliations_add_1(self):
		self.mio.acl_publisher_add(self.NODE_EXAMPLE, "testnode1")
		real = self.mio.acl_affiliations_query(self.NODE_EXAMPLE)
		expected = [
			{'affiliation': 'owner',
			'jid': 'testuser@sensor.andrew.cmu.edu'},
			{'affiliation': 'publisher',
			'jid': 'testnode1'}]
		real.sort()
		expected.sort()
		self.assertEqual(expected, real)

	def test_acl_affiliations_add_2(self):
		self.mio.acl_publisher_add(self.NODE_EXAMPLE, "testnode1")
		self.mio.acl_publisher_add(self.NODE_EXAMPLE, "testnode2")
		real = self.mio.acl_affiliations_query(self.NODE_EXAMPLE)
		expected = [
			{'affiliation': 'owner',
			'jid': 'testuser@sensor.andrew.cmu.edu'},
			{'affiliation': 'publisher',
			'jid': 'testnode1'},
			{'affiliation': 'publisher',
			'jid': 'testnode2'}]

		real.sort(key=lambda x:(x["affiliation"],x["jid"]))
		expected.sort(key=lambda x:(x["affiliation"],x["jid"]))
		self.assertEqual(expected, real)

	def test_acl_affiliations_remove(self):
		self.mio.acl_publisher_add(self.NODE_EXAMPLE, "testnode1")
		self.mio.acl_publisher_add(self.NODE_EXAMPLE, "testnode2")
		self.mio.acl_publisher_remove(self.NODE_EXAMPLE, "testnode1")
		real = self.mio.acl_affiliations_query(self.NODE_EXAMPLE)
		expected = [
			{'affiliation': 'owner',
			'jid': 'testuser@sensor.andrew.cmu.edu'},
			{'affiliation': 'publisher',
			'jid': 'testnode2'}]
		real.sort()
		expected.sort()
		self.assertEqual(expected, real)


if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(TestMetaData)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_acl_affiliations_remove_1"))
	#runner = unittest.TextTestRunner()
	#runner.run(suite)