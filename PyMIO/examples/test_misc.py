#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import unittest
import logging
import uuid

from mio import MIO
from mio_types import Unit, MetaType


if __name__ == '__main__':

	mio = MIO("testuser","sensor.andrew.cmu.edu","testuser",
		log_level=logging.DEBUG)

	mio.node_delete("8c3bfe10-dc9d-11e4-b061-0bb9c619e5ea")
	mio.node_create("8c3bfe10-dc9d-11e4-b061-0bb9c619e5ea")
	#mio.collection_children_query("8c3bfe10-dc9d-11e4-b061-0bb9c619e5ea")

	mio.stop()