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

class TestCollections(unittest.TestCase):

	COLL1	= str(uuid.uuid4())
	COLL2	= str(uuid.uuid4())
	CHILD1	= str(uuid.uuid4())
	CHILD2	= str(uuid.uuid4())

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")
		#self.mio.node_create(self.COLL1) #TODO to collection
		#self.mio.node_create(self.COLL2) #TODO to collection
		#self.mio.node_create(self.CHILD1)
		#self.mio.node_create(self.CHILD2)

	def tearDown(self):
		self.mio.node_delete(self.COLL1)
		self.mio.node_delete(self.COLL2)
		self.mio.node_delete(self.CHILD1)
		self.mio.node_delete(self.CHILD2)
		self.mio.stop()

	def test_collection_add(self):
		
		self.mio.collection_node_create(self.COLL1, "collection_One")
		self.mio.coll_query(self.COLL1)


		#todo
		#self.mio.add_test_fileds("coll1")

		#self.mio.coll_query("coll1")


		#self.mio.collection_child_add("coll1", "child1")
		
		#print self.mio.CLIENT['xep_0060'].get_item(self.mio.SERVER, "coll1", "pubsub#collection")


		#real = self.mio.collection_children_query("coll1")
		#print real

if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(TestCollections)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_acl_affiliations_remove_1"))
	#runner = unittest.TextTestRunner()
	#runner.run(suite)