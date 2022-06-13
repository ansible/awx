import React from 'react';
import { act } from 'react-dom/test-utils';
import { shallow, mount } from 'enzyme';
import useJobEvents, {
  jobEventsReducer,
  ADD_EVENTS,
  TOGGLE_NODE_COLLAPSED,
} from './useJobEvents';

function Child() {
  return <div />;
}
function HookTest({
  fetchEventByUuid = () => {},
  fetchChildrenSummary = () => {},
  setForceFlatMode = () => {},
  setJobTreeReady = () => {},
  jobId = 1,
  isFlatMode = false,
}) {
  const hookFuncs = useJobEvents(
    {
      fetchEventByUuid,
      fetchChildrenSummary,
      setForceFlatMode,
      setJobTreeReady,
    },
    jobId,
    isFlatMode
  );
  return <Child id="test" {...hookFuncs} />;
}

const eventsList = [
  {
    id: 101,
    counter: 1,
    rowNumber: 0,
    uuid: 'abc-001',
    event_level: 0,
    parent_uuid: '',
  },
  {
    id: 102,
    counter: 2,
    rowNumber: 1,
    uuid: 'abc-002',
    event_level: 1,
    parent_uuid: 'abc-001',
  },
  {
    id: 103,
    counter: 3,
    rowNumber: 2,
    uuid: 'abc-003',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 104,
    counter: 4,
    rowNumber: 3,
    uuid: 'abc-004',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 105,
    counter: 5,
    rowNumber: 4,
    uuid: 'abc-005',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 106,
    counter: 6,
    rowNumber: 5,
    uuid: 'abc-006',
    event_level: 1,
    parent_uuid: 'abc-001',
  },
  {
    id: 107,
    counter: 7,
    rowNumber: 6,
    uuid: 'abc-007',
    event_level: 2,
    parent_uuid: 'abc-006',
  },
  {
    id: 108,
    counter: 8,
    rowNumber: 7,
    uuid: 'abc-008',
    event_level: 2,
    parent_uuid: 'abc-006',
  },
  {
    id: 109,
    counter: 9,
    rowNumber: 8,
    uuid: 'abc-009',
    event_level: 2,
    parent_uuid: 'abc-006',
  },
];
const basicEvents = {
  1: eventsList[0],
  2: eventsList[1],
  3: eventsList[2],
  4: eventsList[3],
  5: eventsList[4],
  6: eventsList[5],
  7: eventsList[6],
  8: eventsList[7],
  9: eventsList[8],
};
const basicTree = [
  {
    eventIndex: 1,
    isCollapsed: false,
    children: [
      {
        eventIndex: 2,
        isCollapsed: false,
        children: [
          { eventIndex: 3, isCollapsed: false, children: [] },
          { eventIndex: 4, isCollapsed: false, children: [] },
          { eventIndex: 5, isCollapsed: false, children: [] },
        ],
      },
      {
        eventIndex: 6,
        isCollapsed: false,
        children: [
          { eventIndex: 7, isCollapsed: false, children: [] },
          { eventIndex: 8, isCollapsed: false, children: [] },
          { eventIndex: 9, isCollapsed: false, children: [] },
        ],
      },
    ],
  },
];

describe('useJobEvents', () => {
  let callbacks;
  let reducer;
  let emptyState;
  let enqueueAction;

  beforeEach(() => {
    callbacks = {
      fetchEventByUuid: jest.fn(),
      fetchChildrenSummary: jest.fn(),
      setForceFlatMode: jest.fn(),
      setJobTreeReady: jest.fn(),
    };
    enqueueAction = jest.fn();
    reducer = jobEventsReducer(callbacks, false, enqueueAction);
    emptyState = {
      tree: [],
      events: {},
      uuidMap: {},
      eventsWithoutParents: {},
      childrenSummary: {},
      metaEventParentUuid: {},
      eventGaps: [],
      isAllCollapsed: false,
    };
  });

  afterAll(() => {
    jest.resetAllMocks();
  });

  describe('addEvents', () => {
    test('should build initial tree', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      expect(state.events).toEqual(basicEvents);
      expect(state.tree).toEqual(basicTree);
      expect(state.uuidMap).toEqual({
        'abc-001': 1,
        'abc-002': 2,
        'abc-003': 3,
        'abc-004': 4,
        'abc-005': 5,
        'abc-006': 6,
        'abc-007': 7,
        'abc-008': 8,
        'abc-009': 9,
      });
    });

    test('should append new events', () => {
      const newEvents = [
        {
          id: 110,
          counter: 10,
          rowNumber: 9,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 111,
          counter: 11,
          rowNumber: 10,
          uuid: 'abc-011',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 112,
          counter: 12,
          rowNumber: 11,
          uuid: 'abc-012',
          event_level: 0,
          parent_uuid: '',
        },
      ];
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      const { events, tree } = reducer(state, {
        type: ADD_EVENTS,
        events: newEvents,
      });

      expect(events).toEqual({
        1: eventsList[0],
        2: eventsList[1],
        3: eventsList[2],
        4: eventsList[3],
        5: eventsList[4],
        6: eventsList[5],
        7: eventsList[6],
        8: eventsList[7],
        9: eventsList[8],
        10: newEvents[0],
        11: newEvents[1],
        12: newEvents[2],
      });
      expect(tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [
                { eventIndex: 3, isCollapsed: false, children: [] },
                { eventIndex: 4, isCollapsed: false, children: [] },
                { eventIndex: 5, isCollapsed: false, children: [] },
              ],
            },
            {
              eventIndex: 6,
              isCollapsed: false,
              children: [
                { eventIndex: 7, isCollapsed: false, children: [] },
                { eventIndex: 8, isCollapsed: false, children: [] },
                { eventIndex: 9, isCollapsed: false, children: [] },
                { eventIndex: 10, isCollapsed: false, children: [] },
              ],
            },
            {
              eventIndex: 11,
              isCollapsed: false,
              children: [],
            },
          ],
        },
        { eventIndex: 12, isCollapsed: false, children: [] },
      ]);
    });

    test('should not mutate original state', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: [eventsList[0], eventsList[1]],
      });
      window.debug = true;
      reducer(state, {
        type: ADD_EVENTS,
        events: [eventsList[2], eventsList[5]],
      });

      expect(state.events).toEqual({ 1: eventsList[0], 2: eventsList[1] });
      expect(state.tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [],
            },
          ],
        },
      ]);
      expect(state.uuidMap).toEqual({
        'abc-001': 1,
        'abc-002': 2,
      });
    });

    test('should not duplicate events in events tree', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      const newNode = {
        id: 110,
        counter: 10,
        rowNumber: 9,
        uuid: 'abc-010',
        event_level: 2,
        parent_uuid: 'abc-006',
      };
      reducer(state, {
        type: ADD_EVENTS,
        events: [newNode],
      });
      const { events, tree } = reducer(state, {
        type: ADD_EVENTS,
        events: [newNode],
      });

      expect(events).toEqual({
        1: eventsList[0],
        2: eventsList[1],
        3: eventsList[2],
        4: eventsList[3],
        5: eventsList[4],
        6: eventsList[5],
        7: eventsList[6],
        8: eventsList[7],
        9: eventsList[8],
        10: newNode,
      });
      expect(tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [
                { eventIndex: 3, isCollapsed: false, children: [] },
                { eventIndex: 4, isCollapsed: false, children: [] },
                { eventIndex: 5, isCollapsed: false, children: [] },
              ],
            },
            {
              eventIndex: 6,
              isCollapsed: false,
              children: [
                { eventIndex: 7, isCollapsed: false, children: [] },
                { eventIndex: 8, isCollapsed: false, children: [] },
                { eventIndex: 9, isCollapsed: false, children: [] },
                { eventIndex: 10, isCollapsed: false, children: [] },
              ],
            },
          ],
        },
      ]);
    });

    test('should fetch parent for events with missing parent', async () => {
      callbacks.fetchEventByUuid.mockResolvedValue({
        counter: 10,
      });
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            10: [9, 2],
          },
        },
        {
          type: ADD_EVENTS,
          events: eventsList,
        }
      );

      const newEvents = [
        {
          id: 112,
          counter: 12,
          rowNumber: 11,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      reducer(state, { type: ADD_EVENTS, events: newEvents });

      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-010');
    });

    test('should batch parent fetches by uuid', () => {
      callbacks.fetchEventByUuid.mockResolvedValue({
        counter: 10,
      });
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            10: [9, 2],
          },
        },
        {
          type: ADD_EVENTS,
          events: eventsList,
        }
      );

      const newEvents = [
        {
          id: 112,
          counter: 12,
          rowNumber: 11,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
        {
          id: 113,
          counter: 13,
          rowNumber: 12,
          uuid: 'abc-013',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      reducer(state, { type: ADD_EVENTS, events: newEvents });

      expect(callbacks.fetchEventByUuid).toHaveBeenCalledTimes(1);
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-010');
    });

    test('should fetch multiple parent fetches by uuid', () => {
      callbacks.fetchEventByUuid.mockResolvedValue({
        counter: 10,
      });
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            10: [9, 1],
          },
        },
        {
          type: ADD_EVENTS,
          events: eventsList,
        }
      );

      const newEvents = [
        {
          id: 114,
          counter: 14,
          rowNumber: 13,
          uuid: 'abc-014',
          event_level: 2,
          parent_uuid: 'abc-012',
        },
        {
          id: 115,
          counter: 15,
          rowNumber: 14,
          uuid: 'abc-015',
          event_level: 1,
          parent_uuid: 'abc-011',
        },
      ];
      reducer(state, { type: ADD_EVENTS, events: newEvents });

      expect(callbacks.fetchEventByUuid).toHaveBeenCalledTimes(2);
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-012');
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-011');
    });

    test('should set eventsWithoutParents while fetching parent events', () => {
      callbacks.fetchEventByUuid.mockResolvedValue({
        counter: 10,
      });
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            10: [9, 2],
          },
        },
        {
          type: ADD_EVENTS,
          events: eventsList,
        }
      );

      const newEvents = [
        {
          id: 112,
          counter: 12,
          rowNumber: 11,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      const { eventsWithoutParents, tree } = reducer(state, {
        type: ADD_EVENTS,
        events: newEvents,
      });

      expect(eventsWithoutParents).toEqual({
        'abc-010': [newEvents[0]],
      });
      expect(tree).toEqual(basicTree);
    });

    test('should check for eventsWithoutParents belonging to new nodes', () => {
      const childEvent = {
        id: 112,
        counter: 12,
        rowNumber: 11,
        uuid: 'abc-012',
        event_level: 1,
        parent_uuid: 'abc-010',
      };
      const initialState = {
        ...emptyState,
        eventsWithoutParents: {
          'abc-010': [childEvent],
        },
      };
      const parentEvent = {
        id: 110,
        counter: 10,
        rowNumber: 9,
        uuid: 'abc-010',
        event_level: 0,
        parent_uuid: '',
      };

      const { tree, events, eventsWithoutParents } = reducer(initialState, {
        type: ADD_EVENTS,
        events: [parentEvent],
      });

      expect(tree).toEqual([
        {
          eventIndex: 10,
          isCollapsed: false,
          children: [
            {
              eventIndex: 12,
              isCollapsed: false,
              children: [],
            },
          ],
        },
      ]);
      expect(events).toEqual({
        10: parentEvent,
        12: childEvent,
      });
      expect(eventsWithoutParents).toEqual({});
    });

    test('should fetch parent of parent and compile them together', () => {
      callbacks.fetchEventByUuid.mockResolvedValueOnce({
        counter: 2,
      });
      callbacks.fetchEventByUuid.mockResolvedValueOnce({
        counter: 1,
      });
      const event3 = {
        id: 103,
        counter: 3,
        rowNumber: 2,
        uuid: 'abc-003',
        event_level: 2,
        parent_uuid: 'abc-002',
      };
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            1: [0, 3],
            2: [1, 2],
          },
        },
        {
          type: ADD_EVENTS,
          events: [event3],
        }
      );
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-002');

      const event2 = {
        id: 102,
        counter: 2,
        rowNumber: 1,
        uuid: 'abc-002',
        event_level: 1,
        parent_uuid: 'abc-001',
      };
      const state2 = reducer(state, {
        type: ADD_EVENTS,
        events: [event2],
      });
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-001');
      expect(state2.events).toEqual({});
      expect(state2.tree).toEqual([]);
      expect(state2.eventsWithoutParents).toEqual({
        'abc-001': [event2],
        'abc-002': [event3],
      });

      const event1 = {
        id: 101,
        counter: 1,
        rowNumber: 0,
        uuid: 'abc-001',
        event_level: 0,
        parent_uuid: '',
      };
      const state3 = reducer(state2, {
        type: ADD_EVENTS,
        events: [event1],
      });
      expect(state3.events).toEqual({
        1: event1,
        2: event2,
        3: event3,
      });
      expect(state3.tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [
                {
                  eventIndex: 3,
                  isCollapsed: false,
                  children: [],
                },
              ],
            },
          ],
        },
      ]);
      expect(state3.eventsWithoutParents).toEqual({});
    });

    test('should add root level node in middle of array', () => {
      const events = [
        {
          id: 101,
          counter: 1,
          rowNumber: 0,
          uuid: 'abc-001',
          event_level: 0,
          parent_uuid: '',
        },
        {
          id: 102,
          counter: 2,
          rowNumber: 1,
          uuid: 'abc-002',
          event_level: 0,
          parent_uuid: '',
        },
        {
          id: 103,
          counter: 3,
          rowNumber: 2,
          uuid: 'abc-003',
          event_level: 0,
          parent_uuid: '',
        },
      ];
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: [events[0]],
      });
      const state2 = reducer(state, {
        type: ADD_EVENTS,
        events: [events[2]],
      });
      const state3 = reducer(state2, {
        type: ADD_EVENTS,
        events: [events[1]],
      });

      expect(state3.tree[0].eventIndex).toEqual(1);
      expect(state3.tree[1].eventIndex).toEqual(2);
      expect(state3.tree[2].eventIndex).toEqual(3);
    });

    test('should add child nodes in middle of array', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: [...eventsList.slice(0, 3), ...eventsList.slice(4)],
      });
      const state2 = reducer(state, {
        type: ADD_EVENTS,
        events: [eventsList[3]],
      });

      expect(state2.tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [
                { eventIndex: 3, isCollapsed: false, children: [] },
                { eventIndex: 4, isCollapsed: false, children: [] },
                { eventIndex: 5, isCollapsed: false, children: [] },
              ],
            },
            {
              eventIndex: 6,
              isCollapsed: false,
              children: [
                { eventIndex: 7, isCollapsed: false, children: [] },
                { eventIndex: 8, isCollapsed: false, children: [] },
                { eventIndex: 9, isCollapsed: false, children: [] },
              ],
            },
          ],
        },
      ]);
    });

    test('should build in flat mode', () => {
      const flatReducer = jobEventsReducer(callbacks, true, enqueueAction);
      const state = flatReducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      expect(state.events).toEqual(basicEvents);
      expect(state.tree).toEqual([
        { eventIndex: 1, isCollapsed: false, children: [] },
        { eventIndex: 2, isCollapsed: false, children: [] },
        { eventIndex: 3, isCollapsed: false, children: [] },
        { eventIndex: 4, isCollapsed: false, children: [] },
        { eventIndex: 5, isCollapsed: false, children: [] },
        { eventIndex: 6, isCollapsed: false, children: [] },
        { eventIndex: 7, isCollapsed: false, children: [] },
        { eventIndex: 8, isCollapsed: false, children: [] },
        { eventIndex: 9, isCollapsed: false, children: [] },
      ]);
      expect(state.uuidMap).toEqual({
        'abc-001': 1,
        'abc-002': 2,
        'abc-003': 3,
        'abc-004': 4,
        'abc-005': 5,
        'abc-006': 6,
        'abc-007': 7,
        'abc-008': 8,
        'abc-009': 9,
      });
    });

    test('should nest "meta" event based on given parent uuid', () => {
      const state = reducer(
        {
          ...emptyState,
          childrenSummary: {
            2: { rowNumber: 1, numChildren: 3 },
          },
          metaEventParentUuid: {
            4: 'abc-002',
          },
        },
        {
          type: ADD_EVENTS,
          events: [...eventsList.slice(0, 3)],
        }
      );
      const state2 = reducer(state, {
        type: ADD_EVENTS,
        events: [
          {
            counter: 4,
            rowNumber: 3,
            parent_uuid: '',
          },
        ],
      });

      expect(state2.tree).toEqual([
        {
          eventIndex: 1,
          isCollapsed: false,
          children: [
            {
              eventIndex: 2,
              isCollapsed: false,
              children: [
                { eventIndex: 3, isCollapsed: false, children: [] },
                { eventIndex: 4, isCollapsed: false, children: [] },
              ],
            },
          ],
        },
      ]);
    });
  });

  describe('getNodeByUuid', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should get a root node', () => {
      const node = wrapper.find('#test').prop('getNodeByUuid')('abc-001');
      expect(node.eventIndex).toEqual(1);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(2);
    });

    test('should get 2nd level node', () => {
      const node = wrapper.find('#test').prop('getNodeByUuid')('abc-002');
      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(3);
    });

    test('should get 3rd level node', () => {
      const node = wrapper.find('#test').prop('getNodeByUuid')('abc-008');
      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(0);
    });

    test('should return null if node not found', () => {
      const node = wrapper.find('#test').prop('getNodeByUuid')('abc-028');
      expect(node).toEqual(null);
    });
  });

  describe('toggleNodeIsCollapsed', () => {
    test('should collapse node', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      const { tree } = reducer(state, {
        type: TOGGLE_NODE_COLLAPSED,
        uuid: 'abc-001',
      });

      expect(tree).toEqual([
        {
          ...basicTree[0],
          isCollapsed: true,
        },
      ]);
    });

    test('should expand node', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      const { tree } = reducer(
        {
          ...state,
          tree: [
            {
              ...state.tree[0],
              isCollapsed: true,
            },
          ],
        },
        {
          type: TOGGLE_NODE_COLLAPSED,
          uuid: 'abc-001',
        }
      );

      expect(tree).toEqual(basicTree);
    });
  });

  describe('getNodeForRow', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should get root node', () => {
      const node = wrapper.find('#test').prop('getNodeForRow')(0);

      expect(node.eventIndex).toEqual(1);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(2);
    });

    test('should get 2nd level node', () => {
      const node = wrapper.find('#test').prop('getNodeForRow')(1);

      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(3);
    });

    test('should get 3rd level node', () => {
      const node = wrapper.find('#test').prop('getNodeForRow')(7);

      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(0);
    });

    test('should get last child node', () => {
      const node = wrapper.find('#test').prop('getNodeForRow')(4);

      expect(node.eventIndex).toEqual(5);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(0);
    });

    test('should get a second root-level node', () => {
      const lastNode = {
        id: 110,
        counter: 10,
        rowNumber: 9,
        uuid: 'abc-010',
        event_level: 0,
        parent_uuid: '',
      };
      wrapper.find('#test').prop('addEvents')([lastNode]);

      const node = wrapper.find('#test').prop('getNodeForRow')(9);

      expect(node).toEqual({
        eventIndex: 10,
        isCollapsed: false,
        children: [],
      });
    });

    test('should return null if no node matches index', () => {
      const node = wrapper.find('#test').prop('getNodeForRow')(10);

      expect(node).toEqual(null);
    });

    test('should return null if no nodes loaded', () => {
      wrapper = shallow(<HookTest />);
      const node = wrapper.find('#test').prop('getNodeForRow')(5);

      expect(node).toEqual(null);
    });

    test('should return collapsed node', () => {
      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');

      const node = wrapper.find('#test').prop('getNodeForRow')(1);

      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toBe(true);
    });

    test('should skip nodes with collapsed parent', () => {
      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');

      const node = wrapper.find('#test').prop('getNodeForRow')(2);
      expect(node.eventIndex).toEqual(6);
      expect(node.isCollapsed).toBe(false);

      const node2 = wrapper.find('#test').prop('getNodeForRow')(4);
      expect(node2.eventIndex).toEqual(8);
      expect(node2.isCollapsed).toBe(false);
    });

    test('should skip deeply-nested collapsed nodes', () => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')([
        { id: 101, counter: 1, rowNumber: 0, uuid: 'abc-001', event_level: 0 },
        {
          id: 102,
          counter: 2,
          rowNumber: 1,
          uuid: 'abc-002',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 103,
          counter: 3,
          rowNumber: 2,
          uuid: 'abc-003',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 104,
          counter: 4,
          rowNumber: 3,
          uuid: 'abc-004',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 105,
          counter: 5,
          rowNumber: 4,
          uuid: 'abc-005',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 106,
          counter: 6,
          rowNumber: 5,
          uuid: 'abc-006',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 107,
          counter: 7,
          rowNumber: 6,
          uuid: 'abc-007',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 108,
          counter: 8,
          rowNumber: 7,
          uuid: 'abc-008',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 109,
          counter: 9,
          rowNumber: 8,
          uuid: 'abc-009',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
        {
          id: 110,
          counter: 10,
          rowNumber: 9,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
      ]);
      wrapper.update();
      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-004');
      wrapper.update();

      const node = wrapper.find('#test').prop('getNodeForRow')(5);
      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toBe(false);
    });

    test('should skip full sub-tree of collapsed node', () => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')([
        { id: 101, counter: 1, rowNumber: 0, uuid: 'abc-001', event_level: 0 },
        {
          id: 102,
          counter: 2,
          rowNumber: 1,
          uuid: 'abc-002',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 103,
          counter: 3,
          rowNumber: 2,
          uuid: 'abc-003',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 104,
          counter: 4,
          rowNumber: 3,
          uuid: 'abc-004',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 105,
          counter: 5,
          rowNumber: 4,
          uuid: 'abc-005',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 106,
          counter: 6,
          rowNumber: 5,
          uuid: 'abc-006',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 107,
          counter: 7,
          rowNumber: 6,
          uuid: 'abc-007',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 108,
          counter: 8,
          rowNumber: 7,
          uuid: 'abc-008',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 109,
          counter: 9,
          rowNumber: 8,
          uuid: 'abc-009',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
        {
          id: 110,
          counter: 10,
          rowNumber: 9,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
      ]);
      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');

      const node = wrapper.find('#test').prop('getNodeForRow')(3);
      expect(node.eventIndex).toEqual(9);
      expect(node.isCollapsed).toBe(false);
    });

    test('should get node after gap in loaded children', async () => {
      const fetchChildrenSummary = jest.fn();
      fetchChildrenSummary.mockResolvedValue({
        data: {
          children_summary: {
            1: { rowNumber: 0, numChildren: 52 },
            2: { rowNumber: 1, numChildren: 3 },
            6: { rowNumber: 5, numChildren: 47 },
          },
          meta_event_nested_uuid: {},
        },
      });

      wrapper = mount(<HookTest fetchChildrenSummary={fetchChildrenSummary} />);
      const laterEvents = [
        {
          id: 151,
          counter: 51,
          rowNumber: 50,
          uuid: 'abc-051',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 152,
          counter: 52,
          rowNumber: 51,
          uuid: 'abc-052',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 153,
          counter: 53,
          rowNumber: 52,
          uuid: 'abc-052',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
      ];
      await act(async () => {
        wrapper.find('#test').prop('addEvents')(eventsList);
        wrapper.find('#test').prop('addEvents')(laterEvents);
      });
      wrapper.update();
      wrapper.update();

      const node = wrapper.find('#test').prop('getNodeForRow')(51);
      expect(node).toEqual({
        eventIndex: 52,
        isCollapsed: false,
        children: [],
      });
    });

    test('should skip gaps in counter', () => {
      const nextNode = {
        id: 112,
        counter: 12,
        rowNumber: 9,
        uuid: 'abc-012',
        event_level: 0,
        parent_uuid: '',
      };
      wrapper.find('#test').prop('addEvents')([nextNode]);

      const node = wrapper.find('#test').prop('getNodeForRow')(9);

      expect(node).toEqual({
        eventIndex: 12,
        isCollapsed: false,
        children: [],
      });
    });
  });

  describe('getNumCollapsedEvents', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should return number of collapsed events', () => {
      expect(wrapper.find('#test').prop('getNumCollapsedEvents')()).toEqual(0);

      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');
      expect(wrapper.find('#test').prop('getNumCollapsedEvents')()).toEqual(3);
    });
  });

  describe('getEventforRow', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should get event & node', () => {
      const { event, node } = wrapper.find('#test').prop('getEventForRow')(5);
      expect(event).toEqual(eventsList[5]);
      expect(node).toEqual({
        eventIndex: 6,
        isCollapsed: false,
        children: [
          { eventIndex: 7, isCollapsed: false, children: [] },
          { eventIndex: 8, isCollapsed: false, children: [] },
          { eventIndex: 9, isCollapsed: false, children: [] },
        ],
      });
    });
  });

  describe('getEvent', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should get event object', () => {
      const event = wrapper.find('#test').prop('getEvent')(7);
      expect(event).toEqual(eventsList[6]);
    });
  });

  describe('getTotalNumChildren', () => {
    let wrapper;

    test('should not make call to get child events, because there are none for this job type', () => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      expect(callbacks.fetchChildrenSummary).not.toBeCalled();
    });

    test('should get basic number of children', () => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      expect(
        wrapper.find('#test').prop('getTotalNumChildren')('abc-002')
      ).toEqual(3);
    });

    test('should get total number of nested children', () => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      expect(
        wrapper.find('#test').prop('getTotalNumChildren')('abc-001')
      ).toEqual(8);
    });
  });

  describe('getCounterForRow', () => {
    test('should return exact counter when no nodes are collapsed', () => {
      const wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(8)).toEqual(9);
    });

    test('should return estimated counter when node not loaded', () => {
      const wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(12)).toEqual(13);
    });

    test('should return estimated counter when node is non-loaded child', async () => {
      callbacks.fetchChildrenSummary.mockResolvedValue({
        data: {
          1: { rowNumber: 0, numChildren: 28 },
          2: { rowNumber: 1, numChildren: 3 },
          6: { rowNumber: 5, numChidren: 23 },
        },
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      wrapper.update();
      await act(async () => {
        wrapper.find('#test').prop('addEvents')(eventsList);
        wrapper.find('#test').prop('addEvents')([
          {
            id: 130,
            counter: 30,
            rowNumber: 29,
            uuid: 'abc-030',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
        ]);
      });
      wrapper.update();

      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');

      expect(getCounterForRow(15)).toEqual(16);
    });

    test('should skip over collapsed subtree', () => {
      const wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
      wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');
      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(4)).toEqual(8);
    });

    test('should estimate counter after skipping collapsed subtree', async () => {
      callbacks.fetchChildrenSummary.mockResolvedValue({
        data: {
          children_summary: {
            1: { rowNumber: 0, numChildren: 85 },
            2: { rowNumber: 1, numChildren: 66 },
            69: { rowNumber: 68, numChildren: 17 },
          },
          meta_event_nested_uuid: {},
        },
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          eventsList[1],
          eventsList[2],
          eventsList[3],
          eventsList[4],
          {
            id: 169,
            counter: 69,
            rowNumber: 68,
            event_level: 2,
            uuid: 'abc-069',
            parent_uuid: 'abc-001',
          },
        ]);
        wrapper.find('#test').prop('toggleNodeIsCollapsed')('abc-002');
      });
      wrapper.update();

      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(3)).toEqual(70);
    });

    test('should estimate counter in gap between loaded events', async () => {
      callbacks.fetchChildrenSummary.mockResolvedValue({
        data: {
          children_summary: {
            1: { rowNumber: 0, numChildren: 30 },
          },
          meta_event_nested_uuid: {},
        },
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 102,
            counter: 2,
            rowNumber: 1,
            uuid: 'abc-002',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 103,
            counter: 3,
            rowNumber: 2,
            uuid: 'abc-003',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 120,
            counter: 20,
            rowNumber: 19,
            uuid: 'abc-020',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 121,
            counter: 21,
            rowNumber: 20,
            uuid: 'abc-021',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 122,
            counter: 22,
            rowNumber: 21,
            uuid: 'abc-022',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
        ]);
      });
      wrapper.update();

      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(10)).toEqual(11);
    });

    test('should estimate counter in gap before loaded sibling events', async () => {
      callbacks.fetchChildrenSummary.mockResolvedValue({
        data: {
          children_summary: {
            1: { rowNumber: 0, numChildren: 30 },
          },
          meta_event_nested_uuid: {},
        },
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 120,
            counter: 20,
            rowNumber: 19,
            uuid: 'abc-020',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 121,
            counter: 21,
            rowNumber: 20,
            uuid: 'abc-021',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 122,
            counter: 22,
            rowNumber: 21,
            uuid: 'abc-022',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
        ]);
      });
      wrapper.update();

      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(10)).toEqual(11);
    });

    test('should get counter for node between unloaded siblings', async () => {
      callbacks.fetchChildrenSummary.mockResolvedValue({
        data: {
          children_summary: {
            1: { rowNumber: 0, numChildren: 30 },
          },
          meta_event_nested_uuid: {},
        },
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 109,
            counter: 9,
            rowNumber: 8,
            uuid: 'abc-009',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 110,
            counter: 10,
            rowNumber: 9,
            uuid: 'abc-010',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 111,
            counter: 11,
            rowNumber: 10,
            uuid: 'abc-011',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
        ]);
      });
      wrapper.update();

      const getCounterForRow = wrapper.find('#test').prop('getCounterForRow');
      expect(getCounterForRow(10)).toEqual(11);
    });
  });
});
