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

# MIO Schedule example test

import unittest
import uuid

from mio import MIO
from mio_types import MetaType


class Test(unittest.TestCase):

	SCHED_EXE = str(uuid.uuid4())

	def setUp(self):
		self.mio = MIO("testuser","sensor.andrew.cmu.edu","testuser")

		# Create metaexample node"
		self.mio.node_create(self.SCHED_EXE)

	def tearDown(self):
		# Delete scheduleexample node if it is already present"
		self.mio.node_delete(self.SCHED_EXE)
		self.mio.stop()


	def test_schedule_add_1(self):
		# Add schedule event
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 22,
			"2014-08-22T14:00:00.412338-0500", info="First test event",
			recurrence_frequency="daily",recurrence_interval=1,
			recurrence_count=5, recurrence_until="Monday", recurrence_bymonth=1,
			recurrence_byday=2, recurrence_exdate="Monday")

		real = self.mio.schedule_query(self.SCHED_EXE)
		expected = [{
			'info': 'First test event',
			'transducerName': 'atrasducer',
			'recurrence': {
				'count': '5',
				'byday': '2',
				'bymonth': '1',
				'interval': '1',
				'exdate': 'Monday',
				'freq': 'daily',
				'until': 'Monday'},
			'time': '2014-08-22T14:00:00.412338-0500',
			'transducerValue': '22',
			'id': '0'}]

		self.assertEqual(expected, real)
	
	def test_schedule_add_2(self):
		# Add three schedule events

		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 1,
			"2014-08-22T14:00:00.412331-0500", info="First test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 2,
			"2014-08-22T14:00:00.412332-0500", info="Second test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 3,
			"2014-08-22T14:00:00.412333-0500", info="Third test event")

		# Check if all events were added"
		real = self.mio.schedule_query(self.SCHED_EXE)
		expected = [
			{	'info': 'First test event',
				'transducerValue': '1',
				'transducerName': 'atrasducer',
				'id': '0',
				'time': '2014-08-22T14:00:00.412331-0500'
			},
			{	'info': 'Second test event',
				'transducerValue': '2',
				'transducerName': 'atrasducer',
				'id': '1',
				'time': '2014-08-22T14:00:00.412332-0500'
			},
			{	'info': 'Third test event',
				'transducerValue': '3',
				'transducerName': 'atrasducer',
				'id': '2',
				'time': '2014-08-22T14:00:00.412333-0500'}]
		
		real.sort()
		expected.sort()

		self.assertEqual(expected, real)

	def test_schedule_update(self):
		# Add three schedule events
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 1,
			"2014-08-22T14:00:00.412331-0500", info="First test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 2,
			"2014-08-22T14:00:00.412332-0500", info="Second test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 3,
			"2014-08-22T14:00:00.412333-0500", info="Third test event")

		# Update the time and transducer value of event with ID 1"
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 4,
			'2014-08-22T14:00:00.412334-0500', event_id=1)


		# Check if all events were added"
		real = self.mio.schedule_query(self.SCHED_EXE)
		expected = [
			{	'info': 'First test event',
				'transducerValue': '1',
				'transducerName': 'atrasducer',
				'id': '0',
				'time': '2014-08-22T14:00:00.412331-0500'
			},
			{	'info': 'Second test event',
				'transducerValue': '4',
				'transducerName': 'atrasducer',
				'id': '1',
				'time': '2014-08-22T14:00:00.412334-0500'
			},
			{	'info': 'Third test event',
				'transducerValue': '3',
				'transducerName': 'atrasducer',
				'id': '2',
				'time': '2014-08-22T14:00:00.412333-0500'}]
		
		real.sort()
		expected.sort()

		self.assertEqual(expected, real)

	def test_schedule_remove(self):
		# Add three schedule events
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 1,
			"2014-08-22T14:00:00.412331-0500", info="First test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 2,
			"2014-08-22T14:00:00.412332-0500", info="Second test event")
		self.mio.schedule_event_add(self.SCHED_EXE, "atrasducer", 3,
			"2014-08-22T14:00:00.412333-0500", info="Third test event")

		# Check if all events were added
		real = self.mio.schedule_query(self.SCHED_EXE)
		expected = [
			{	'info': 'First test event',
				'transducerValue': '1',
				'transducerName': 'atrasducer',
				'id': '0',
				'time': '2014-08-22T14:00:00.412331-0500'
			},
			{	'info': 'Second test event',
				'transducerValue': '2',
				'transducerName': 'atrasducer',
				'id': '1',
				'time': '2014-08-22T14:00:00.412332-0500'
			},
			{	'info': 'Third test event',
				'transducerValue': '3',
				'transducerName': 'atrasducer',
				'id': '2',
				'time': '2014-08-22T14:00:00.412333-0500'}]
		
		real.sort()
		expected.sort()
		self.assertEqual(expected, real)

		# Remove event with id 1
		self.mio.schedule_event_remove(self.SCHED_EXE, event_id=1)

		# Check if event 1 was removed
		real = self.mio.schedule_query(self.SCHED_EXE)
		expected = [
			{	'info': 'First test event',
				'transducerValue': '1',
				'transducerName': 'atrasducer',
				'id': '0',
				'time': '2014-08-22T14:00:00.412331-0500'
			},
			{	'info': 'Third test event',
				'transducerValue': '3',
				'transducerName': 'atrasducer',
				'id': '1',
				'time': '2014-08-22T14:00:00.412333-0500'}]
		
		real.sort()
		expected.sort()
		self.assertEqual(expected, real)


if __name__ == '__main__':

	suite = unittest.TestLoader().loadTestsFromTestCase(Test)
	unittest.TextTestRunner(verbosity=2).run(suite)

	#suite = unittest.TestSuite()
	#suite.addTest(TestMetaData("test_acl_affiliations_remove_1"))
	#runner = unittest.TextTestRunner()
	#runner.run(suite)