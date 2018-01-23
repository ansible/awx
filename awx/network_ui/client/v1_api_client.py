
import requests

import util
import json


def list_device(**kwargs):
    response = requests.get(util.get_url() + "/device/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_device(device_id):
    response = requests.get(util.get_url() + "/device/" + str(device_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_device(topology, name, x, y, id, type, interface_id_seq=0, process_id_seq=0, host_id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/device/", data=json.dumps(dict(topology=topology,
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
    response = requests.patch(util.get_url() + "/device/" + str(device_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_device(device_id):
    response = requests.delete(util.get_url() + "/device/" + str(device_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_link(**kwargs):
    response = requests.get(util.get_url() + "/link/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_link(link_id):
    response = requests.get(util.get_url() + "/link/" + str(link_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_link(from_device, to_device, from_interface, to_interface, id, name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/link/", data=json.dumps(dict(from_device=from_device,
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
    response = requests.patch(util.get_url() + "/link/" + str(link_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_link(link_id):
    response = requests.delete(util.get_url() + "/link/" + str(link_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topology(**kwargs):
    response = requests.get(util.get_url() + "/topology/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_topology(topology_id):
    response = requests.get(util.get_url() + "/topology/" + str(topology_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topology(name, scale, panX, panY, device_id_seq=0, link_id_seq=0, group_id_seq=0, stream_id_seq=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/topology/", data=json.dumps(dict(name=name,
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
    response = requests.patch(util.get_url() + "/topology/" + str(topology_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topology(topology_id):
    response = requests.delete(util.get_url() + "/topology/" + str(topology_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_client(**kwargs):
    response = requests.get(util.get_url() + "/client/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_client(client_id):
    response = requests.get(util.get_url() + "/client/" + str(client_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_client():
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/client/", data=json.dumps(dict()),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_client(client_id, ):
    headers = {'content-type': 'application/json'}
    data = dict()
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/client/" + str(client_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_client(client_id):
    response = requests.delete(util.get_url() + "/client/" + str(client_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topologyhistory(**kwargs):
    response = requests.get(util.get_url() + "/topologyhistory/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_topologyhistory(topology_history_id):
    response = requests.get(util.get_url() + "/topologyhistory/" + str(topology_history_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topologyhistory(topology, client, message_type, message_id, message_data, undone=False,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/topologyhistory/", data=json.dumps(dict(topology=topology,
                                                                                        client=client,
                                                                                        message_type=message_type,
                                                                                        message_id=message_id,
                                                                                        message_data=message_data,
                                                                                        undone=undone,
                                                                                        )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_topologyhistory(topology_history_id, topology=None, client=None, message_type=None, message_id=None, message_data=None, undone=None,):
    headers = {'content-type': 'application/json'}
    data = dict(topology=topology,
                client=client,
                message_type=message_type,
                message_id=message_id,
                message_data=message_data,
                undone=undone,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/topologyhistory/" + str(topology_history_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topologyhistory(topology_history_id):
    response = requests.delete(util.get_url() + "/topologyhistory/" + str(topology_history_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_messagetype(**kwargs):
    response = requests.get(util.get_url() + "/messagetype/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_messagetype(message_type_id):
    response = requests.get(util.get_url() + "/messagetype/" + str(message_type_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_messagetype(name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/messagetype/", data=json.dumps(dict(name=name,
                                                                                    )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_messagetype(message_type_id, name=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/messagetype/" + str(message_type_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_messagetype(message_type_id):
    response = requests.delete(util.get_url() + "/messagetype/" + str(message_type_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_interface(**kwargs):
    response = requests.get(util.get_url() + "/interface/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_interface(interface_id):
    response = requests.get(util.get_url() + "/interface/" + str(interface_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_interface(device, name, id,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/interface/", data=json.dumps(dict(device=device,
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
    response = requests.patch(util.get_url() + "/interface/" + str(interface_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_interface(interface_id):
    response = requests.delete(util.get_url() + "/interface/" + str(interface_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_group(**kwargs):
    response = requests.get(util.get_url() + "/group/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_group(group_id):
    response = requests.get(util.get_url() + "/group/" + str(group_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_group(id, name, x1, y1, x2, y2, topology, type,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/group/", data=json.dumps(dict(id=id,
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
    response = requests.patch(util.get_url() + "/group/" + str(group_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_group(group_id):
    response = requests.delete(util.get_url() + "/group/" + str(group_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_groupdevice(**kwargs):
    response = requests.get(util.get_url() + "/groupdevice/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_groupdevice(group_device_id):
    response = requests.get(util.get_url() + "/groupdevice/" + str(group_device_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_groupdevice(group, device,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/groupdevice/", data=json.dumps(dict(group=group,
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
    response = requests.patch(util.get_url() + "/groupdevice/" + str(group_device_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_groupdevice(group_device_id):
    response = requests.delete(util.get_url() + "/groupdevice/" + str(group_device_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_databinding(**kwargs):
    response = requests.get(util.get_url() + "/databinding/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_databinding(data_binding_id):
    response = requests.get(util.get_url() + "/databinding/" + str(data_binding_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_databinding(column, row, table, primary_key_id, field, data_type, sheet,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/databinding/", data=json.dumps(dict(column=column,
                                                                                    row=row,
                                                                                    table=table,
                                                                                    primary_key_id=primary_key_id,
                                                                                    field=field,
                                                                                    data_type=data_type,
                                                                                    sheet=sheet,
                                                                                    )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_databinding(data_binding_id, column=None, row=None, table=None, primary_key_id=None, field=None, data_type=None, sheet=None,):
    headers = {'content-type': 'application/json'}
    data = dict(column=column,
                row=row,
                table=table,
                primary_key_id=primary_key_id,
                field=field,
                data_type=data_type,
                sheet=sheet,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/databinding/" + str(data_binding_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_databinding(data_binding_id):
    response = requests.delete(util.get_url() + "/databinding/" + str(data_binding_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_datatype(**kwargs):
    response = requests.get(util.get_url() + "/datatype/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_datatype(data_type_id):
    response = requests.get(util.get_url() + "/datatype/" + str(data_type_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_datatype(type_name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/datatype/", data=json.dumps(dict(type_name=type_name,
                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_datatype(data_type_id, type_name=None,):
    headers = {'content-type': 'application/json'}
    data = dict(type_name=type_name,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/datatype/" + str(data_type_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_datatype(data_type_id):
    response = requests.delete(util.get_url() + "/datatype/" + str(data_type_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_datasheet(**kwargs):
    response = requests.get(util.get_url() + "/datasheet/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_datasheet(data_sheet_id):
    response = requests.get(util.get_url() + "/datasheet/" + str(data_sheet_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_datasheet(name, topology, client,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/datasheet/", data=json.dumps(dict(name=name,
                                                                                  topology=topology,
                                                                                  client=client,
                                                                                  )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_datasheet(data_sheet_id, name=None, topology=None, client=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                topology=topology,
                client=client,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/datasheet/" + str(data_sheet_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_datasheet(data_sheet_id):
    response = requests.delete(util.get_url() + "/datasheet/" + str(data_sheet_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_stream(**kwargs):
    response = requests.get(util.get_url() + "/stream/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_stream(stream_id):
    response = requests.get(util.get_url() + "/stream/" + str(stream_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_stream(from_device, to_device, label, id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/stream/", data=json.dumps(dict(from_device=from_device,
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
    response = requests.patch(util.get_url() + "/stream/" + str(stream_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_stream(stream_id):
    response = requests.delete(util.get_url() + "/stream/" + str(stream_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_process(**kwargs):
    response = requests.get(util.get_url() + "/process/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_process(process_id):
    response = requests.get(util.get_url() + "/process/" + str(process_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_process(device, name, type, id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/process/", data=json.dumps(dict(device=device,
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
    response = requests.patch(util.get_url() + "/process/" + str(process_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_process(process_id):
    response = requests.delete(util.get_url() + "/process/" + str(process_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_toolbox(**kwargs):
    response = requests.get(util.get_url() + "/toolbox/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_toolbox(toolbox_id):
    response = requests.get(util.get_url() + "/toolbox/" + str(toolbox_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_toolbox(name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/toolbox/", data=json.dumps(dict(name=name,
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
    response = requests.patch(util.get_url() + "/toolbox/" + str(toolbox_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_toolbox(toolbox_id):
    response = requests.delete(util.get_url() + "/toolbox/" + str(toolbox_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_toolboxitem(**kwargs):
    response = requests.get(util.get_url() + "/toolboxitem/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_toolboxitem(toolbox_item_id):
    response = requests.get(util.get_url() + "/toolboxitem/" + str(toolbox_item_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_toolboxitem(toolbox, data,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/toolboxitem/", data=json.dumps(dict(toolbox=toolbox,
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
    response = requests.patch(util.get_url() + "/toolboxitem/" + str(toolbox_item_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_toolboxitem(toolbox_item_id):
    response = requests.delete(util.get_url() + "/toolboxitem/" + str(toolbox_item_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_fsmtrace(**kwargs):
    response = requests.get(util.get_url() + "/fsmtrace/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_fsmtrace(fsm_trace_id):
    response = requests.get(util.get_url() + "/fsmtrace/" + str(fsm_trace_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_fsmtrace(fsm_name, from_state, to_state, message_type, client, trace_session_id=0, order=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/fsmtrace/", data=json.dumps(dict(fsm_name=fsm_name,
                                                                                 from_state=from_state,
                                                                                 to_state=to_state,
                                                                                 message_type=message_type,
                                                                                 client=client,
                                                                                 trace_session_id=trace_session_id,
                                                                                 order=order,
                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_fsmtrace(fsm_trace_id, fsm_name=None, from_state=None, to_state=None, message_type=None, client=None, trace_session_id=None, order=None,):
    headers = {'content-type': 'application/json'}
    data = dict(fsm_name=fsm_name,
                from_state=from_state,
                to_state=to_state,
                message_type=message_type,
                client=client,
                trace_session_id=trace_session_id,
                order=order,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/fsmtrace/" + str(fsm_trace_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_fsmtrace(fsm_trace_id):
    response = requests.delete(util.get_url() + "/fsmtrace/" + str(fsm_trace_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topologyinventory(**kwargs):
    response = requests.get(util.get_url() + "/topologyinventory/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_topologyinventory(topology_inventory_id):
    response = requests.get(util.get_url() + "/topologyinventory/" + str(topology_inventory_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topologyinventory(topology, inventory_id,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/topologyinventory/", data=json.dumps(dict(topology=topology,
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
    response = requests.patch(util.get_url() + "/topologyinventory/" + str(topology_inventory_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topologyinventory(topology_inventory_id):
    response = requests.delete(util.get_url() + "/topologyinventory/" + str(topology_inventory_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_eventtrace(**kwargs):
    response = requests.get(util.get_url() + "/eventtrace/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_eventtrace(event_trace_id):
    response = requests.get(util.get_url() + "/eventtrace/" + str(event_trace_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_eventtrace(client, event_data, message_id, trace_session_id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/eventtrace/", data=json.dumps(dict(client=client,
                                                                                   trace_session_id=trace_session_id,
                                                                                   event_data=event_data,
                                                                                   message_id=message_id,
                                                                                   )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_eventtrace(event_trace_id, client=None, trace_session_id=None, event_data=None, message_id=None,):
    headers = {'content-type': 'application/json'}
    data = dict(client=client,
                trace_session_id=trace_session_id,
                event_data=event_data,
                message_id=message_id,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/eventtrace/" + str(event_trace_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_eventtrace(event_trace_id):
    response = requests.delete(util.get_url() + "/eventtrace/" + str(event_trace_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_coverage(**kwargs):
    response = requests.get(util.get_url() + "/coverage/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_coverage(coverage_id):
    response = requests.get(util.get_url() + "/coverage/" + str(coverage_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_coverage(coverage_data, test_result,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/coverage/", data=json.dumps(dict(coverage_data=coverage_data,
                                                                                 test_result=test_result,
                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_coverage(coverage_id, coverage_data=None, test_result=None,):
    headers = {'content-type': 'application/json'}
    data = dict(coverage_data=coverage_data,
                test_result=test_result,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/coverage/" + str(coverage_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_coverage(coverage_id):
    response = requests.delete(util.get_url() + "/coverage/" + str(coverage_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_topologysnapshot(**kwargs):
    response = requests.get(util.get_url() + "/topologysnapshot/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_topologysnapshot(topology_snapshot_id):
    response = requests.get(util.get_url() + "/topologysnapshot/" + str(topology_snapshot_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_topologysnapshot(client, topology_id, trace_session_id, snapshot_data, order,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/topologysnapshot/", data=json.dumps(dict(client=client,
                                                                                         topology_id=topology_id,
                                                                                         trace_session_id=trace_session_id,
                                                                                         snapshot_data=snapshot_data,
                                                                                         order=order,
                                                                                         )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_topologysnapshot(topology_snapshot_id, client=None, topology_id=None, trace_session_id=None, snapshot_data=None, order=None,):
    headers = {'content-type': 'application/json'}
    data = dict(client=client,
                topology_id=topology_id,
                trace_session_id=trace_session_id,
                snapshot_data=snapshot_data,
                order=order,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/topologysnapshot/" + str(topology_snapshot_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_topologysnapshot(topology_snapshot_id):
    response = requests.delete(util.get_url() + "/topologysnapshot/" + str(topology_snapshot_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_testcase(**kwargs):
    response = requests.get(util.get_url() + "/testcase/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_testcase(test_case_id):
    response = requests.get(util.get_url() + "/testcase/" + str(test_case_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_testcase(name, test_case_data,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/testcase/", data=json.dumps(dict(name=name,
                                                                                 test_case_data=test_case_data,
                                                                                 )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_testcase(test_case_id, name=None, test_case_data=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                test_case_data=test_case_data,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/testcase/" + str(test_case_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_testcase(test_case_id):
    response = requests.delete(util.get_url() + "/testcase/" + str(test_case_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_result(**kwargs):
    response = requests.get(util.get_url() + "/result/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_result(result_id):
    response = requests.get(util.get_url() + "/result/" + str(result_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_result(name,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/result/", data=json.dumps(dict(name=name,
                                                                               )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_result(result_id, name=None,):
    headers = {'content-type': 'application/json'}
    data = dict(name=name,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/result/" + str(result_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_result(result_id):
    response = requests.delete(util.get_url() + "/result/" + str(result_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_codeundertest(**kwargs):
    response = requests.get(util.get_url() + "/codeundertest/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_codeundertest(code_under_test_id):
    response = requests.get(util.get_url() + "/codeundertest/" + str(code_under_test_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_codeundertest(version_x, version_y, version_z, commits_since, commit_hash,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/codeundertest/", data=json.dumps(dict(version_x=version_x,
                                                                                      version_y=version_y,
                                                                                      version_z=version_z,
                                                                                      commits_since=commits_since,
                                                                                      commit_hash=commit_hash,
                                                                                      )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_codeundertest(code_under_test_id, version_x=None, version_y=None, version_z=None, commits_since=None, commit_hash=None,):
    headers = {'content-type': 'application/json'}
    data = dict(version_x=version_x,
                version_y=version_y,
                version_z=version_z,
                commits_since=commits_since,
                commit_hash=commit_hash,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/codeundertest/" + str(code_under_test_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_codeundertest(code_under_test_id):
    response = requests.delete(util.get_url() + "/codeundertest/" + str(code_under_test_id), verify=util.get_verify(), auth=util.get_auth())
    return response


def list_testresult(**kwargs):
    response = requests.get(util.get_url() + "/testresult/", verify=util.get_verify(), auth=util.get_auth(), params=kwargs)
    return response.json()


def get_testresult(test_result_id):
    response = requests.get(util.get_url() + "/testresult/" + str(test_result_id), verify=util.get_verify(), auth=util.get_auth())
    return response.json()


def create_testresult(test_case, result, code_under_test, time, client, id=0,):
    headers = {'content-type': 'application/json'}
    response = requests.post(util.get_url() + "/testresult/", data=json.dumps(dict(test_case=test_case,
                                                                                   result=result,
                                                                                   code_under_test=code_under_test,
                                                                                   time=time,
                                                                                   id=id,
                                                                                   client=client,
                                                                                   )),
                             verify=util.get_verify(),
                             auth=util.get_auth(),
                             headers=headers)
    return response.json()


def update_testresult(test_result_id, test_case=None, result=None, code_under_test=None, time=None, id=None, client=None,):
    headers = {'content-type': 'application/json'}
    data = dict(test_case=test_case,
                result=result,
                code_under_test=code_under_test,
                time=time,
                id=id,
                client=client,
                )
    data = {x: y for x, y in data.iteritems() if y is not None}
    response = requests.patch(util.get_url() + "/testresult/" + str(test_result_id) + "/",
                              data=json.dumps(data),
                              verify=util.get_verify(),
                              auth=util.get_auth(),
                              headers=headers)
    return response


def delete_testresult(test_result_id):
    response = requests.delete(util.get_url() + "/testresult/" + str(test_result_id), verify=util.get_verify(), auth=util.get_auth())
    return response
