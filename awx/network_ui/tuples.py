

from collections import namedtuple


Device = namedtuple('Device', ['device_id',
                               'topology',
                               'name',
                               'x',
                               'y',
                               'id',
                               'type',
                               'interface_id_seq',
                               'process_id_seq',
                               'host_id',
                               ])

Link = namedtuple('Link', ['link_id',
                           'from_device',
                           'to_device',
                           'from_interface',
                           'to_interface',
                           'id',
                           'name',
                           ])

Topology = namedtuple('Topology', ['topology_id',
                                   'name',
                                   'scale',
                                   'panX',
                                   'panY',
                                   'device_id_seq',
                                   'link_id_seq',
                                   'group_id_seq',
                                   'stream_id_seq',
                                   ])

Client = namedtuple('Client', ['client_id',
                               ])

TopologyHistory = namedtuple('TopologyHistory', ['topology_history_id',
                                                 'topology',
                                                 'client',
                                                 'message_type',
                                                 'message_id',
                                                 'message_data',
                                                 'undone',
                                                 ])

MessageType = namedtuple('MessageType', ['message_type_id',
                                         'name',
                                         ])

Interface = namedtuple('Interface', ['interface_id',
                                     'device',
                                     'name',
                                     'id',
                                     ])

Group = namedtuple('Group', ['group_id',
                             'id',
                             'name',
                             'x1',
                             'y1',
                             'x2',
                             'y2',
                             'topology',
                             'type',
                             'inventory_group_id',
                             ])

GroupDevice = namedtuple('GroupDevice', ['group_device_id',
                                         'group',
                                         'device',
                                         ])

DataBinding = namedtuple('DataBinding', ['data_binding_id',
                                         'column',
                                         'row',
                                         'table',
                                         'primary_key_id',
                                         'field',
                                         'data_type',
                                         'sheet',
                                         ])

DataType = namedtuple('DataType', ['data_type_id',
                                   'type_name',
                                   ])

DataSheet = namedtuple('DataSheet', ['data_sheet_id',
                                     'name',
                                     'topology',
                                     'client',
                                     ])

Stream = namedtuple('Stream', ['stream_id',
                               'from_device',
                               'to_device',
                               'label',
                               'id',
                               ])

Process = namedtuple('Process', ['process_id',
                                 'device',
                                 'name',
                                 'type',
                                 'id',
                                 ])

Toolbox = namedtuple('Toolbox', ['toolbox_id',
                                 'name',
                                 ])

ToolboxItem = namedtuple('ToolboxItem', ['toolbox_item_id',
                                         'toolbox',
                                         'data',
                                         ])

FSMTrace = namedtuple('FSMTrace', ['fsm_trace_id',
                                   'fsm_name',
                                   'from_state',
                                   'to_state',
                                   'message_type',
                                   'client',
                                   'trace_session_id',
                                   'order',
                                   ])

TopologyInventory = namedtuple('TopologyInventory', ['topology_inventory_id',
                                                     'topology',
                                                     'inventory_id',
                                                     ])

EventTrace = namedtuple('EventTrace', ['event_trace_id',
                                       'client',
                                       'trace_session_id',
                                       'event_data',
                                       'message_id',
                                       ])

Coverage = namedtuple('Coverage', ['coverage_id',
                                   'coverage_data',
                                   'test_result',
                                   ])

TopologySnapshot = namedtuple('TopologySnapshot', ['topology_snapshot_id',
                                                   'client',
                                                   'topology_id',
                                                   'trace_session_id',
                                                   'snapshot_data',
                                                   'order',
                                                   ])

TestCase = namedtuple('TestCase', ['test_case_id',
                                   'name',
                                   'test_case_data',
                                   ])

Result = namedtuple('Result', ['result_id',
                               'name',
                               ])

CodeUnderTest = namedtuple('CodeUnderTest', ['code_under_test_id',
                                             'version_x',
                                             'version_y',
                                             'version_z',
                                             'commits_since',
                                             'commit_hash',
                                             ])

TestResult = namedtuple('TestResult', ['test_result_id',
                                       'test_case',
                                       'result',
                                       'code_under_test',
                                       'time',
                                       'id',
                                       'client',
                                       ])
