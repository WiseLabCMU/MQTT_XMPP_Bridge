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

# MIO Reference example test

import unittest
import uuid

from mio import MIO
from mio_types import MetaType, ReferenceType


class TestMetaData(unittest.TestCase):

	PARENT1 = str(uuid.uuid4())
	PARENT2 = str(uuid.uuid4())
	CHILD1 	= str(uuid.uuid4())
	CHILD2 	= str(uuid.uuid4())
	CHILD3 	= str(uuid.uuid4())

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")
		
		
		# Create example nodes
		self.mio.node_create(self.PARENT1)
		self.mio.node_create(self.PARENT2)
		self.mio.node_create(self.CHILD1)
		self.mio.node_create(self.CHILD2)
		self.mio.node_create(self.CHILD3)

		# Populate nodes with meta data so that the meta_type references for each
		# reference can be populated
		self.mio.meta_add(self.PARENT1, meta_name="refparent1",
			node_type=MetaType.DEVICE, info="This node contains a device")
		self.mio.meta_add(self.PARENT2, meta_name="refparent2",
			node_type=MetaType.LOCATION, info="This node contains a location")
		
		self.mio.meta_add(self.CHILD1, meta_name="refchild1",
			node_type=MetaType.DEVICE, info="This node contains a device")
		self.mio.meta_add(self.CHILD2, meta_name="refchild2",
			node_type=MetaType.DEVICE, info="This node contains a device")
		self.mio.meta_add(self.CHILD3, meta_name="refchild3",
			node_type=MetaType.DEVICE, info="This node contains a device")

	def tearDown(self):
		# Remove example nodes if they already exist
		self.mio.node_delete(self.PARENT1)
		self.mio.node_delete(self.PARENT2)
		self.mio.node_delete(self.CHILD1)
		self.mio.node_delete(self.CHILD2)
		self.mio.node_delete(self.CHILD3)
		self.mio.stop()


	def test_reference_add_parent(self):
		# Add all three children to refparent1
		# And check if children were added corrctly
		# The children should not have reference to the parent
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1)
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD2)
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD3)

		expected_children = [self.CHILD1, self.CHILD2, self.CHILD3]
		real_refs = self.mio.reference_query(self.PARENT1)
		real_list= list()
		for item in real_refs:
			if item["type"] == ReferenceType.CHILD.value:
				real_list.append(item["node"])

		real_list.sort()
		expected_children.sort()

		self.assertEqual(real_list, expected_children)

		#The children must not have reference to parent
		self.assertEqual(list(), self.mio.reference_query(self.CHILD1))
		self.assertEqual(list(), self.mio.reference_query(self.CHILD2))
		self.assertEqual(list(), self.mio.reference_query(self.CHILD3))


	def test_reference_add_child_1(self):
		# Add all three children to refparent1
		# The children 1 and 3 should have reference to the parent
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1,
			add_ref_child=True)
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD2)
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD3,
			add_ref_child=True)


		#Only the child 1 and 3 must have reference to parent
		child1_refs = self.mio.reference_query(self.CHILD1)
		child2_refs = self.mio.reference_query(self.CHILD2)
		child3_refs = self.mio.reference_query(self.CHILD3)
		
		self.assertEqual(child1_refs[0]["node"], self.PARENT1)
		self.assertEqual(child1_refs[0]["type"], ReferenceType.PARENT.value)

		self.assertEqual(child2_refs, list())

		self.assertEqual(child3_refs[0]["node"], self.PARENT1)
		self.assertEqual(child3_refs[0]["type"], ReferenceType.PARENT.value)
		
	
	def test_reference_add_child_2(self):
		# Add refparent1 as the child of refparent2"
		self.mio.reference_child_add(parent=self.PARENT2, child=self.PARENT1,
			add_ref_child=True)

		# Check if the parent1 is child of parent2
		parent2_ref = self.mio.reference_query(self.PARENT2)
		self.assertEqual(parent2_ref[0]["node"], self.PARENT1)
		self.assertEqual(parent2_ref[0]["type"], ReferenceType.CHILD.value)

		# Check to see if refparent2 is the parent of refparent1
		parent1_ref = self.mio.reference_query(self.PARENT1)
		self.assertEqual(parent1_ref[0]["node"], self.PARENT2)
		self.assertEqual(parent1_ref[0]["type"], ReferenceType.PARENT.value)


	def test_reference_remove_1(self):
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1)

		# Reference must be present on the parent but not on the child
		parent_refs = self.mio.reference_query(self.PARENT1)
		child_refs = self.mio.reference_query(self.CHILD1)
		self.assertEqual(parent_refs[0]["node"], self.CHILD1)
		self.assertEqual(parent_refs[0]["type"], ReferenceType.CHILD.value)
		self.assertEqual(child_refs, list())

		# Remove refchild1 from refparent1
		self.mio.reference_child_remove(parent=self.PARENT1, child=self.CHILD1)

		# Check to see if refchild1 has been removed from the parent
		# No references must exists between the two
		parent_refs = self.mio.reference_query(self.PARENT1)
		child_refs = self.mio.reference_query(self.CHILD1)
		self.assertEqual(parent_refs, list())
		self.assertEqual(child_refs, list())

	def test_reference_remove_2(self):
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1,
			add_ref_child=True)

		# Reference must be present on the parent and child
		parent_refs = self.mio.reference_query(self.PARENT1)
		child_refs = self.mio.reference_query(self.CHILD1)
		self.assertEqual(parent_refs[0]["node"], self.CHILD1)
		self.assertEqual(parent_refs[0]["type"], ReferenceType.CHILD.value)
		self.assertEqual(child_refs[0]["node"], self.PARENT1)
		self.assertEqual(child_refs[0]["type"], ReferenceType.PARENT.value)

		# Remove refchild1 from refparent1
		self.mio.reference_child_remove(parent=self.PARENT1, child=self.CHILD1)

		# Check to see if both the references have been removed
		parent_refs = self.mio.reference_query(self.PARENT1)
		child_refs = self.mio.reference_query(self.CHILD1)
		self.assertEqual(parent_refs, list())
		self.assertEqual(child_refs, list())

	def test_reference_meta_type(self):
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1)

		#Check meta type of the child reference
		parent_refs = self.mio.reference_query(self.PARENT1)
		self.assertEqual(parent_refs[0]["metaType"], MetaType.DEVICE.value)

		# Change the meta type of refchild1 to location"
		self.mio.meta_add(self.CHILD1, meta_name="refchild1",
			node_type=MetaType.LOCATION, info="This node contains a location")

		# Check again the reference off the child node
		# Must match with the new node metaType
		parent_refs = self.mio.reference_query(self.PARENT1)
		self.assertEqual(parent_refs[0]["metaType"], MetaType.LOCATION.value)


	def test_reference_meta_type_remove(self):
		self.mio.reference_child_add(parent=self.PARENT1, child=self.CHILD1)

		#Check meta type of the child reference
		parent_refs = self.mio.reference_query(self.PARENT1)
		self.assertEqual(parent_refs[0]["metaType"], MetaType.DEVICE.value)

		# Remove the meta data from refchild1
		self.mio.meta_remove(self.CHILD1)

		# Check to see if meta type is now unknown for refchild1 in the
		# references of parent1
		parent_refs = self.mio.reference_query(self.PARENT1)
		self.assertEqual(parent_refs[0]["metaType"], MetaType.UKNOWN.value)

if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(TestMetaData)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_meta_transducer_remove"))
	#runner = unittest.TextTestRunner()
	#srunner.run(suite)