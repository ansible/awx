
import requests

import util
import json


def list_device(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/device/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_device(device_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/device/" + str(device_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_device(topology, name, x, y, id, type, interface_id_seq=0, process_id_seq=0, host_id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/device/", data=json.dumps(dict(topology=topology,
                                                                                                 name=name,
                                                                                                 x=x,
                                                                                                 y=y,
                                                                                                 id=id,
                                                                                                 type=type,
                                                                                                 interface_id_seq=interface_id_seq,
                                                                                                 process_id_seq=process_id_seq,
                                                                                                 host_id=host_id,
                                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_device(device_id, topology=None, name=None, x=None, y=None, id=None, type=None, interface_id_seq=None, process_id_seq=None, host_id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(topology=topology,
                name=name,
                x=x,
                y=y,
                id=id,
                type=type,
                interface_id_seq=interface_id_seq,
                process_id_seq=process_id_seq,
                host_id=host_id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/device/" + str(device_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_device(device_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/device/" + str(device_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_link(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/link/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_link(link_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/link/" + str(link_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_link(from_device, to_device, from_interface, to_interface, id, name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/link/", data=json.dumps(dict(from_device=from_device,
                                                                                               to_device=to_device,
                                                                                               from_interface=from_interface,
                                                                                               to_interface=to_interface,
                                                                                               id=id,
                                                                                               name=name,
                                                                                               )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_link(link_id, from_device=None, to_device=None, from_interface=None, to_interface=None, id=None, name=None,):
    headers = {'content-type': 'application/json'}
    data = dict(from_device=from_device,
                to_device=to_device,
                from_interface=from_interface,
                to_interface=to_interface,
                id=id,
                name=name,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/link/" + str(link_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_link(link_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/link/" + str(link_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topology(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/topology/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_topology(topology_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/topology/" + str(topology_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topology(name, scale, panX, panY, device_id_seq=0, link_id_seq=0, group_id_seq=0, stream_id_seq=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/topology/", data=json.dumps(dict(name=name,
                                                                                                   scale=scale,
                                                                                                   panX=panX,
                                                                                                   panY=panY,
                                                                                                   device_id_seq=device_id_seq,
                                                                                                   link_id_seq=link_id_seq,
                                                                                                   group_id_seq=group_id_seq,
                                                                                                   stream_id_seq=stream_id_seq,
                                                                                                   )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_topology(topology_id, name=None, scale=None, panX=None, panY=None, device_id_seq=None, link_id_seq=None, group_id_seq=None, stream_id_seq=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                scale=scale,
                panX=panX,
                panY=panY,
                device_id_seq=device_id_seq,
                link_id_seq=link_id_seq,
                group_id_seq=group_id_seq,
                stream_id_seq=stream_id_seq,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/topology/" + str(topology_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topology(topology_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/topology/" + str(topology_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_interface(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/interface/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_interface(interface_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/interface/" + str(interface_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_interface(device, name, id,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/interface/", data=json.dumps(dict(device=device,
                                                                                                    name=name,
                                                                                                    id=id,
                                                                                                    )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_interface(interface_id, device=None, name=None, id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(device=device,
                name=name,
                id=id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/interface/" + str(interface_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_interface(interface_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/interface/" + str(interface_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_group(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/group/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_group(group_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/group/" + str(group_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_group(id, name, x1, y1, x2, y2, topology, type,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/group/", data=json.dumps(dict(id=id,
                                                                                                name=name,
                                                                                                x1=x1,
                                                                                                y1=y1,
                                                                                                x2=x2,
                                                                                                y2=y2,
                                                                                                topology=topology,
                                                                                                type=type,
                                                                                                )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_group(group_id, id=None, name=None, x1=None, y1=None, x2=None, y2=None, topology=None, type=None,):
    headers = {'content-type': 'application/json'}
    data = dict(id=id,
                name=name,
                x1=x1,
                y1=y1,
                x2=x2,
                y2=y2,
                topology=topology,
                type=type,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/group/" + str(group_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_group(group_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/group/" + str(group_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_groupdevice(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/groupdevice/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_groupdevice(group_device_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/groupdevice/" + str(group_device_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_groupdevice(group, device,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/groupdevice/", data=json.dumps(dict(group=group,
                                                                                                      device=device,
                                                                                                      )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_groupdevice(group_device_id, group=None, device=None,):
    headers = {'content-type': 'application/json'}
    data = dict(group=group,
                device=device,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/groupdevice/" + str(group_device_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_groupdevice(group_device_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/groupdevice/" + str(group_device_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_stream(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/stream/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_stream(stream_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/stream/" + str(stream_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_stream(from_device, to_device, label, id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/stream/", data=json.dumps(dict(from_device=from_device,
                                                                                                 to_device=to_device,
                                                                                                 label=label,
                                                                                                 id=id,
                                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_stream(stream_id, from_device=None, to_device=None, label=None, id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(from_device=from_device,
                to_device=to_device,
                label=label,
                id=id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/stream/" + str(stream_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_stream(stream_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/stream/" + str(stream_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_process(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/process/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_process(process_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/process/" + str(process_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_process(device, name, type, id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/process/", data=json.dumps(dict(device=device,
                                                                                                  name=name,
                                                                                                  type=type,
                                                                                                  id=id,
                                                                                                  )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_process(process_id, device=None, name=None, type=None, id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(device=device,
                name=name,
                type=type,
                id=id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/process/" + str(process_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_process(process_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/process/" + str(process_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_toolbox(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/toolbox/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_toolbox(toolbox_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/toolbox/" + str(toolbox_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_toolbox(name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/toolbox/", data=json.dumps(dict(name=name,
                                                                                                  )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_toolbox(toolbox_id, name=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/toolbox/" + str(toolbox_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_toolbox(toolbox_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/toolbox/" + str(toolbox_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_toolboxitem(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/toolboxitem/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_toolboxitem(toolbox_item_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/toolboxitem/" + str(toolbox_item_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_toolboxitem(toolbox, data,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/toolboxitem/", data=json.dumps(dict(toolbox=toolbox,
                                                                                                      data=data,
                                                                                                      )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_toolboxitem(toolbox_item_id, toolbox=None, data=None,):
    headers = {'content-type': 'application/json'}
    data = dict(toolbox=toolbox,
                data=data,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/toolboxitem/" + str(toolbox_item_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_toolboxitem(toolbox_item_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/toolboxitem/" + str(toolbox_item_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topologyinventory(**kwargs):
    response = util.unpaginate(util.get_url(), '/network_ui/api/v1/topologyinventory/', util.get_verify(), util.get_auth(), kwargs)
    return response


def get_topologyinventory(topology_inventory_id):
    response = requests.get(util.get_url() + "/network_ui/api/v1/topologyinventory/" +
                            str(topology_inventory_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topologyinventory(topology, inventory_id,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/network_ui/api/v1/topologyinventory/", data=json.dumps(dict(topology=topology,
                                                                                                            inventory_id=inventory_id,
                                                                                                            )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_topologyinventory(topology_inventory_id, topology=None, inventory_id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(topology=topology,
                inventory_id=inventory_id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/network_ui/api/v1/topologyinventory/" + str(topology_inventory_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topologyinventory(topology_inventory_id):
    response = requests.delete(util.get_url() + "/network_ui/api/v1/topologyinventory/" +
                               str(topology_inventory_id), verify=util.get_verify(), auth=util.get_auth())
    return response
