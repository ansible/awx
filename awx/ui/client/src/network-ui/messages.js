/* Copyright (c) 2017 Red Hat, Inc. */


function serialize(message) {
    return JSON.stringify([message.constructor.name, message]);
}
exports.serialize = serialize;

function DeviceMove(sender, id, x, y, previous_x, previous_y) {
    this.msg_type = "DeviceMove";
    this.sender = sender;
    this.id = id;
    this.x = x;
    this.y = y;
    this.previous_x = previous_x;
    this.previous_y = previous_y;
}
exports.DeviceMove = DeviceMove;

function DeviceInventoryUpdate(sender, id, host_id) {
    this.msg_type = "DeviceInventoryUpdate";
    this.sender = sender;
    this.id = id;
    this.host_id = host_id;
}
exports.DeviceInventoryUpdate = DeviceInventoryUpdate;

function DeviceCreate(sender, id, x, y, name, type, host_id) {
    this.msg_type = "DeviceCreate";
    this.sender = sender;
    this.id = id;
    this.x = x;
    this.y = y;
    this.name = name;
    this.type = type;
    this.host_id = host_id;
}
exports.DeviceCreate = DeviceCreate;

function DeviceDestroy(sender, id, previous_x, previous_y, previous_name, previous_type, previous_host_id) {
    this.msg_type = "DeviceDestroy";
    this.sender = sender;
    this.id = id;
    this.previous_x = previous_x;
    this.previous_y = previous_y;
    this.previous_name = previous_name;
    this.previous_type = previous_type;
    this.previous_host_id = previous_host_id;
}
exports.DeviceDestroy = DeviceDestroy;

function DeviceLabelEdit(sender, id, name, previous_name) {
    this.msg_type = "DeviceLabelEdit";
    this.sender = sender;
    this.id = id;
    this.name = name;
    this.previous_name = previous_name;
}
exports.DeviceLabelEdit = DeviceLabelEdit;

function DeviceSelected(sender, id) {
    this.msg_type = "DeviceSelected";
    this.sender = sender;
    this.id = id;
}
exports.DeviceSelected = DeviceSelected;

function DeviceUnSelected(sender, id) {
    this.msg_type = "DeviceUnSelected";
    this.sender = sender;
    this.id = id;
}
exports.DeviceUnSelected = DeviceUnSelected;

function InterfaceCreate(sender, device_id, id, name) {
    this.msg_type = "InterfaceCreate";
    this.sender = sender;
    this.device_id = device_id;
    this.id = id;
    this.name = name;
}
exports.InterfaceCreate = InterfaceCreate;

function InterfaceLabelEdit(sender, id, device_id, name, previous_name) {
    this.msg_type = "InterfaceLabelEdit";
    this.sender = sender;
    this.id = id;
    this.device_id = device_id;
    this.name = name;
    this.previous_name = previous_name;
}
exports.InterfaceLabelEdit = InterfaceLabelEdit;

function LinkLabelEdit(sender, id, name, previous_name) {
    this.msg_type = "LinkLabelEdit";
    this.sender = sender;
    this.id = id;
    this.name = name;
    this.previous_name = previous_name;
}
exports.LinkLabelEdit = LinkLabelEdit;

function LinkCreate(sender, id, from_device_id, to_device_id, from_interface_id, to_interface_id) {
    this.msg_type = "LinkCreate";
    this.id = id;
    this.sender = sender;
    this.name = '';
    this.from_device_id = from_device_id;
    this.to_device_id = to_device_id;
    this.from_interface_id = from_interface_id;
    this.to_interface_id = to_interface_id;
}
exports.LinkCreate = LinkCreate;

function LinkDestroy(sender, id, from_device_id, to_device_id, from_interface_id, to_interface_id, name) {
    this.msg_type = "LinkDestroy";
    this.id = id;
    this.sender = sender;
    this.name = name;
    this.from_device_id = from_device_id;
    this.to_device_id = to_device_id;
    this.from_interface_id = from_interface_id;
    this.to_interface_id = to_interface_id;
}
exports.LinkDestroy = LinkDestroy;

function LinkSelected(sender, id) {
    this.msg_type = "LinkSelected";
    this.sender = sender;
    this.id = id;
}
exports.LinkSelected = LinkSelected;

function LinkUnSelected(sender, id) {
    this.msg_type = "LinkUnSelected";
    this.sender = sender;
    this.id = id;
}
exports.LinkUnSelected = LinkUnSelected;

function MultipleMessage(sender, messages) {
    this.msg_type = "MultipleMessage";
    this.sender = sender;
    this.messages = messages;
}
exports.MultipleMessage = MultipleMessage;


function MouseEvent(sender, x, y, type, trace_id) {
    this.msg_type = "MouseEvent";
    this.sender = sender;
    this.x = x;
    this.y = y;
    this.type = type;
    this.trace_id = trace_id;
}
exports.MouseEvent = MouseEvent;

function MouseWheelEvent(sender, delta, deltaX, deltaY, type, metaKey, trace_id) {
    this.msg_type = "MouseWheelEvent";
    this.sender = sender;
    this.delta = delta;
    this.deltaX = deltaX;
    this.deltaY = deltaY;
    this.type = type;
    this.originalEvent = {metaKey: metaKey};
    this.trace_id = trace_id;
}
exports.MouseWheelEvent = MouseWheelEvent;

function KeyEvent(sender, key, keyCode, type, altKey, shiftKey, ctrlKey, metaKey, trace_id) {
    this.msg_type = "KeyEvent";
    this.sender = sender;
    this.key = key;
    this.keyCode = keyCode;
    this.type = type;
    this.altKey = altKey;
    this.shiftKey = shiftKey;
    this.ctrlKey = ctrlKey;
    this.metaKey = metaKey;
    this.trace_id = trace_id;
}
exports.KeyEvent = KeyEvent;

function StartRecording(sender, trace_id) {
    this.msg_type = "StartRecording";
    this.sender = sender;
    this.trace_id = trace_id;
}
exports.StartRecording = StartRecording;

function StopRecording(sender, trace_id) {
    this.msg_type = "StopRecording";
    this.sender = sender;
    this.trace_id = trace_id;
}
exports.StopRecording = StopRecording;

function ViewPort(sender, scale, panX, panY, trace_id) {
    this.msg_type = "ViewPort";
    this.sender = sender;
    this.scale = scale;
    this.panX = panX;
    this.panY = panY;
    this.trace_id = trace_id;
}
exports.ViewPort = ViewPort;

function NewDevice(type) {
    this.type = type;
}
exports.NewDevice = NewDevice;

function PasteDevice(device) {
    this.device = device;
}
exports.PasteDevice = PasteDevice;

function FSMTrace(order, fsm_name, from_state, to_state, recv_message_type) {
    this.msg_type = 'FSMTrace';
    this.order = order;
    this.sender = 0;
    this.trace_id = 0;
    this.fsm_name = fsm_name;
    this.from_state = from_state;
    this.to_state = to_state;
    this.recv_message_type = recv_message_type;
}
exports.FSMTrace = FSMTrace;

function ChannelTrace(from_fsm, to_fsm, sent_message_type) {
    this.msg_type = 'ChannelTrace';
    this.sender = 0;
    this.trace_id = 0;
    this.from_fsm = from_fsm;
    this.to_fsm = to_fsm;
    this.sent_message_type = sent_message_type;
}
exports.ChannelTrace = ChannelTrace;

function Snapshot(sender, devices, links, order, trace_id) {
    this.msg_type = 'Snapshot';
    this.sender = 0;
    this.devices = devices;
    this.links = links;
    this.order = order;
    this.trace_id = trace_id;
}
exports.Snapshot = Snapshot;

function EnableTest() {
    this.msg_type = "EnableTest";
}
exports.EnableTest = EnableTest;

function DisableTest() {
    this.msg_type = "DisableTest";
}
exports.DisableTest = DisableTest;

function StartTest() {
    this.msg_type = "StartTest";
}
exports.StartTest = StartTest;

function TestCompleted() {
    this.msg_type = "TestCompleted";
}
exports.TestCompleted = TestCompleted;

function TestResult(sender, id, name, result, date, code_under_test) {
    this.msg_type = "TestResult";
    this.sender = sender;
    this.id = id;
    this.name = name;
    this.result = result;
    this.date = date;
    this.code_under_test = code_under_test;
}
exports.TestResult = TestResult;

function Coverage(sender, coverage, result_id) {
    this.msg_type = "Coverage";
    this.sender = sender;
    this.coverage = coverage;
    this.result_id = result_id;
}
exports.Coverage = Coverage;
