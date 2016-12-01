#!/usr/bin/env python


def get_transducer_names_from_meta(node_meta):
        ret_list = list()
        if "children" in node_meta:
                for child in node_meta["children"]:
                         if "transducer" in child.keys():
                                        ret_list.append(child["transducer"]["name"])
        return ret_list


def get_type_property_from_meta(node_meta):
    return get_property_value_from_meta(node_meta,"type")

def get_property_value_from_meta(node_meta, property_name):
	if "children" in node_meta:
		for child in node_meta["children"]:
			if "property" in child.keys():
				if child["property"]["name"] == property_name:
					return child["property"]["value"]	
