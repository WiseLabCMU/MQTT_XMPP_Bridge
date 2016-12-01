#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

################################################################################
#  Mortar IO (MIO) Python2 Library
#
#  Copyright (C) 2014, Carnegie Mellon University
#  All rights reserved.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 2.0 of the License.
#
#  This program is distributed in the hope that it will be useful		= ""
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#  Contributing Authors (specific to this file):
#  Artur Balanuta 		artur[dot]balanuta[at]tecnico[dot]pt
################################################################################

from enum import Enum

## Enum class used to describe Meta Types
class MetaType(Enum):

	UKNOWN		= "unknown"
	DEVICE		= "device"
	LOCATION	= "location"

## Enum class used to describe Reference Types
class ReferenceType(Enum):
	
	UNKNOWN 	= "unknown"
	CHILD		= "child"
	PARENT		= "parent" 

## Enum class used to describe Node Types
class NodeType(Enum):

	UNKNOWN		= "unknown"
	LEAF		= "leaf"
	COLLECTION	= "collection"
	EVENT		= "event"

## Enum class used to describe Device Types
class DeviceType(Enum):

	INDOOR_WEATHER			= "indoor_weather"
	OUTDOOR_WEATHER			= "outdoor_weather"
	HVAC					= "hvac"
	OCCUPANCY				= "occupancy"
	MULTIMEDIA_INPUT		= "multimedia_input"
	MULTIMEDIA_OUTPUT		= "multimedia_output"
	SCALE					= "scale"
	VEHICLE					= "vehicle"
	RESOURCE_CONSUMPTION	= "resource_consumption"
	RESOURCE_GENERATION		= "resource_generation"
	OTHER					= "other"

## Enum class used to describe Unit Types
class Unit(Enum):

	METER						= "meter"
	GRAM						= "gram"
	SECOND						= "second"
	AMPERE						= "ampere"
	KELVIN						= "kelvin"
	MOLE						= "mole"
	CANDELA						= "candela"
	RADIAN						= "radian"
	STERADIAN					= "steradian"
	HERTZ						= "hertz"
	NEWTON						= "newton"
	PASCAL						= "pascal"
	JOULE						= "joule"
	WATT						= "watt"
	COULOMB						= "coulomb"
	VOLT						= "volt"
	FARAD						= "farad"
	OHM							= "ohm"
	SIEMENS						= "siemens"
	WEBER						= "weber"
	TESLA						= "tesla"
	HENRY						= "henry"
	LUMEN						= "lumen"
	LUX							= "lux"
	BECQUEREL					= "becquerel"
	GRAY						= "gray"
	SIEVERT						= "sievert"
	KATAL						= "katal"
	LITER						= "liter"
	SQUARE_METER				= "square_meter"
	CUBIC_METER					= "cubic_meter"
	METERS_PER_SECOND			= "meters_per_second"
	METERS_PER_SECOND_SQUARED	= "meters_per_second_squared"
	RECIPROCAL_METER			= "reciprocal_meter"
	KILOGRAM_PER_CUBIC_METER	= "kilogram_per_cubic_meter"
	CUBIC_METER_PER_KILOGRAM	= "cubic_meter_per_kilogram"
	AMPERE_PER_SQUARE_METER		= "ampere_per_square_meter"
	AMPERE_PER_METER			= "ampere_per_meter"
	MOLE_PER_CUBIC_METER		= "mole_per_cubic_meter"
	CANDELA_PER_SQUARE_METER	= "candela_per_square_meter"
	KILOGRAM_PER_KILOGRAM		= "kilogram_per_kilogram"
	VOLT_AMPERE_REACTIVE		= "volt_ampere_reactive"
	VOLT_AMPERE					= "volt_ampere"
	WATT_SECOND					= "watt_second"
	PERCENT						= "percent"
	ENUM						= "enum"
	LAT							= "lat"
	LON							= "lon"
	CELSIUS						= "degree celsius"
	FARANHIET					= "degree faranhiet"

## Enum class used to describe Affiliation Types
class AffiliationType(Enum):

	NONE			= "none"
	OWNER			= "owner"
	MEMBER			= "member"
	PUBLISHER		= "publisher"
	PUBLISH_ONLY	= "publish_only"
	OUTCAST			= "outcast"
	UKNOWN 			= "unknown"
