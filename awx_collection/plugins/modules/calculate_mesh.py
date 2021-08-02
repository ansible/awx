#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021, Ansible Automation Platform
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


DOCUMENTATION = """
---
module: calculate_mesh
short_description: Calculates the connectivity of the receptor mesh
description:
  - This module inspects the inventory hosts for receptor nodes, expands out the list of
    peers for each node, and does sanity checks for the connectivity of the mesh.
options:
  generate_dot_file:
    description:
      - Output a GraphViz dot-format file that can be rendered to show the graph of the mesh network.
    type: str
    default: mesh.dot
author:
  - Ansible Controller Team
  - Sarabraj Singh
  - Marcelo Moreira de Mello
  - Jeff Bradberry
  - Rebeccah Hunter
"""

EXAMPLES = """
- name: Calculate the receptor mesh connectivity
  awx.awx.calculate_mesh:
  register: mesg
  run_once: true

- name: Output a GraphViz dot file
  awx.awx.calculate_mesh:
    generate_dot_file: /foo/bar/baz.dot
  run_once: true
"""

RETURN = """
mesh:
  description: Information about the receptor mesh nodes and what nodes are peers.
  returned: success
  type: dict
  sample:
    node1:
      node_type: control
      peers:
        - node2
        - node3
    node2:
      node_type: control
      peers:
        - node3
    node3:
      node_type: hybrid
      peers:
"""
