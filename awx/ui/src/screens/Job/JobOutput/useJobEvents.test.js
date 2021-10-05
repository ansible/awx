import React from 'react';
import { act } from 'react-dom/test-utils';
import { shallow, mount } from 'enzyme';
import useJobEvents, {
  jobEventsReducer,
  ADD_EVENTS,
  TOGGLE_NODE_COLLAPSED,
  SET_EVENT_NUM_CHILDREN,
} from './useJobEvents';
import { sleep } from '../../../../testUtils/testUtils';

function Child() {
  return <div />;
}
function HookTest({
  fetchEventByUuid = () => {},
  fetchNextSibling = () => {},
  fetchNextRootNode = () => {},
  fetchNumEvents = () => {},
}) {
  const hookFuncs = useJobEvents({
    fetchEventByUuid,
    fetchNextSibling,
    fetchNextRootNode,
    fetchNumEvents,
  });
  return <Child id="test" {...hookFuncs} />;
}

const eventsList = [
  { id: 101, counter: 1, uuid: 'abc-001', event_level: 0, parent_uuid: '' },
  {
    id: 102,
    counter: 2,
    uuid: 'abc-002',
    event_level: 1,
    parent_uuid: 'abc-001',
  },
  {
    id: 103,
    counter: 3,
    uuid: 'abc-003',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 104,
    counter: 4,
    uuid: 'abc-004',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 105,
    counter: 5,
    uuid: 'abc-005',
    event_level: 2,
    parent_uuid: 'abc-002',
  },
  {
    id: 106,
    counter: 6,
    uuid: 'abc-006',
    event_level: 1,
    parent_uuid: 'abc-001',
  },
  {
    id: 107,
    counter: 7,
    uuid: 'abc-007',
    event_level: 2,
    parent_uuid: 'abc-006',
  },
  {
    id: 108,
    counter: 8,
    uuid: 'abc-008',
    event_level: 2,
    parent_uuid: 'abc-006',
  },
  {
    id: 109,
    counter: 9,
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
      fetchNextSibling: jest.fn(),
      fetchNextRootNode: jest.fn(),
      fetchNumEvents: jest.fn(),
    };
    enqueueAction = jest.fn();
    callbacks.fetchNextSibling.mockResolvedValue(eventsList[9]);
    callbacks.fetchNextRootNode.mockResolvedValue(eventsList[9]);
    reducer = jobEventsReducer(callbacks, enqueueAction);
    emptyState = {
      tree: [],
      events: {},
      uuidMap: {},
      eventsWithoutParents: {},
    };
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
        'abc-001': { index: 1, treePath: [0] },
        'abc-002': { index: 2, treePath: [0, 0] },
        'abc-003': { index: 3, treePath: [0, 0, 0] },
        'abc-004': { index: 4, treePath: [0, 0, 1] },
        'abc-005': { index: 5, treePath: [0, 0, 2] },
        'abc-006': { index: 6, treePath: [0, 1] },
        'abc-007': { index: 7, treePath: [0, 1, 0] },
        'abc-008': { index: 8, treePath: [0, 1, 1] },
        'abc-009': { index: 9, treePath: [0, 1, 2] },
      });
    });

    test('should append new events', () => {
      const newEvents = [
        {
          id: 110,
          counter: 10,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 111,
          counter: 11,
          uuid: 'abc-011',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 112,
          counter: 12,
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
        'abc-001': { index: 1, treePath: [0] },
        'abc-002': { index: 2, treePath: [0, 0] },
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

    test('should fetch parent for events with missing parent', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      const newEvents = [
        {
          id: 112,
          counter: 12,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      reducer(state, { type: ADD_EVENTS, events: newEvents });

      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-010');
    });

    test('should batch parent fetches by uuid', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      const newEvents = [
        {
          id: 112,
          counter: 12,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
        {
          id: 113,
          counter: 13,
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
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      const newEvents = [
        {
          id: 114,
          counter: 14,
          uuid: 'abc-014',
          event_level: 2,
          parent_uuid: 'abc-012',
        },
        {
          id: 115,
          counter: 15,
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
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });

      const newEvents = [
        {
          id: 112,
          counter: 12,
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
      const event3 = {
        id: 103,
        counter: 3,
        uuid: 'abc-003',
        event_level: 2,
        parent_uuid: 'abc-002',
      };
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: [event3],
      });
      expect(callbacks.fetchEventByUuid).toHaveBeenCalledWith('abc-002');

      const event2 = {
        id: 102,
        counter: 2,
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
          uuid: 'abc-001',
          event_level: 0,
          parent_uuid: '',
        },
        {
          id: 102,
          counter: 2,
          uuid: 'abc-002',
          event_level: 0,
          parent_uuid: '',
        },
        {
          id: 103,
          counter: 3,
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

    describe('fetchNumChildren', () => {
      test('should find child count for root node', async () => {
        callbacks.fetchNextRootNode.mockResolvedValue({
          id: 121,
          counter: 21,
          uuid: 'abc-021',
          event_level: 0,
          parent_uuid: '',
        });
        callbacks.fetchNumEvents.mockResolvedValue(19);
        reducer(emptyState, {
          type: ADD_EVENTS,
          events: [eventsList[0], eventsList[1]],
        });

        expect(callbacks.fetchNextSibling).toHaveBeenCalledTimes(0);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledWith(1);
        await sleep(0);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledWith(1, 21);
        expect(enqueueAction).toHaveBeenCalledWith({
          type: SET_EVENT_NUM_CHILDREN,
          uuid: 'abc-001',
          numChildren: 19,
        });
      });

      test('should find child count for last root node', async () => {
        callbacks.fetchNextRootNode.mockResolvedValue(null);
        callbacks.fetchNumEvents.mockResolvedValue(19);
        reducer(emptyState, {
          type: ADD_EVENTS,
          events: [eventsList[0], eventsList[1]],
        });

        expect(callbacks.fetchNextSibling).toHaveBeenCalledTimes(0);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledWith(1);
        await sleep(0);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledWith(1, undefined);
        expect(enqueueAction).toHaveBeenCalledWith({
          type: SET_EVENT_NUM_CHILDREN,
          uuid: 'abc-001',
          numChildren: 19,
        });
      });

      test('should find child count for nested node', async () => {
        const state = {
          events: {
            1: eventsList[0],
            2: eventsList[1],
          },
          tree: [
            {
              children: [{ children: [], eventIndex: 2, isCollapsed: false }],
              eventIndex: 1,
              isCollapsed: false,
            },
          ],
          uuidMap: {
            'abc-001': { index: 1, treePath: [0] },
            'abc-002': { index: 2, treePath: [0, 0] },
          },
          eventsWithoutParents: {},
        };

        callbacks.fetchNextSibling.mockResolvedValue({
          id: 20,
          counter: 20,
          uuid: 'abc-020',
          event_level: 1,
          parent_uuid: 'abc-001',
        });
        callbacks.fetchNumEvents.mockResolvedValue(18);
        reducer(state, {
          type: ADD_EVENTS,
          events: [eventsList[2]],
        });

        expect(callbacks.fetchNextSibling).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNextSibling).toHaveBeenCalledWith(101, 2);
        await sleep(0);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledTimes(0);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledWith(2, 20);
        expect(enqueueAction).toHaveBeenCalledWith({
          type: SET_EVENT_NUM_CHILDREN,
          uuid: 'abc-002',
          numChildren: 18,
        });
      });

      test('should find child count for nested node, last sibling', async () => {
        const state = {
          events: {
            1: eventsList[0],
            2: eventsList[1],
          },
          tree: [
            {
              children: [{ children: [], eventIndex: 2, isCollapsed: false }],
              eventIndex: 1,
              isCollapsed: false,
            },
          ],
          uuidMap: {
            'abc-001': { index: 1, treePath: [0] },
            'abc-002': { index: 2, treePath: [0, 0] },
          },
          eventsWithoutParents: {},
        };

        callbacks.fetchNextSibling.mockResolvedValue(null);
        callbacks.fetchNextRootNode.mockResolvedValue({
          id: 121,
          counter: 21,
          uuid: 'abc-021',
          event_level: 0,
          parent_uuid: '',
        });
        callbacks.fetchNumEvents.mockResolvedValue(19);
        reducer(state, {
          type: ADD_EVENTS,
          events: [eventsList[2]],
        });

        expect(callbacks.fetchNextSibling).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNextSibling).toHaveBeenCalledWith(101, 2);
        await sleep(0);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNextRootNode).toHaveBeenCalledWith(1);
        await sleep(0);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledTimes(1);
        expect(callbacks.fetchNumEvents).toHaveBeenCalledWith(2, 21);
        expect(enqueueAction).toHaveBeenCalledWith({
          type: SET_EVENT_NUM_CHILDREN,
          uuid: 'abc-002',
          numChildren: 19,
        });
      });
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

  describe('setEventNumChildren', () => {
    test('should set number of children on root node', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      expect(state.tree[0].numChildren).toEqual(undefined);

      const { tree } = reducer(state, {
        type: SET_EVENT_NUM_CHILDREN,
        uuid: 'abc-001',
        numChildren: 8,
      });

      expect(tree[0].numChildren).toEqual(8);
    });

    test('should set number of children on nested node', () => {
      const state = reducer(emptyState, {
        type: ADD_EVENTS,
        events: eventsList,
      });
      expect(state.tree[0].numChildren).toEqual(undefined);

      const { tree } = reducer(state, {
        type: SET_EVENT_NUM_CHILDREN,
        uuid: 'abc-006',
        numChildren: 3,
      });

      expect(tree[0].children[1].numChildren).toEqual(3);
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

    test('should get a second root-level node', () => {
      const lastNode = {
        id: 110,
        counter: 10,
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
        { id: 101, counter: 1, uuid: 'abc-001', event_level: 0 },
        {
          id: 102,
          counter: 2,
          uuid: 'abc-002',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 103,
          counter: 3,
          uuid: 'abc-003',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 104,
          counter: 4,
          uuid: 'abc-004',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 105,
          counter: 5,
          uuid: 'abc-005',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 106,
          counter: 6,
          uuid: 'abc-006',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 107,
          counter: 7,
          uuid: 'abc-007',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 108,
          counter: 8,
          uuid: 'abc-008',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 109,
          counter: 9,
          uuid: 'abc-009',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
        {
          id: 110,
          counter: 10,
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
        { id: 101, counter: 1, uuid: 'abc-001', event_level: 0 },
        {
          id: 102,
          counter: 2,
          uuid: 'abc-002',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 103,
          counter: 3,
          uuid: 'abc-003',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 104,
          counter: 4,
          uuid: 'abc-004',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 105,
          counter: 5,
          uuid: 'abc-005',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 106,
          counter: 6,
          uuid: 'abc-006',
          event_level: 3,
          parent_uuid: 'abc-004',
        },
        {
          id: 107,
          counter: 7,
          uuid: 'abc-007',
          event_level: 2,
          parent_uuid: 'abc-002',
        },
        {
          id: 108,
          counter: 8,
          uuid: 'abc-008',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        {
          id: 109,
          counter: 9,
          uuid: 'abc-009',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
        {
          id: 110,
          counter: 10,
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
      const fetchNumEvents = jest.fn();
      fetchNumEvents.mockImplementation((index) => {
        const counts = {
          1: 52,
          2: 3,
          6: 47,
        };
        return Promise.resolve(counts[index]);
      });
      wrapper = mount(<HookTest fetchNumEvents={fetchNumEvents} />);
      const laterEvents = [
        {
          id: 151,
          counter: 51,
          uuid: 'abc-051',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 152,
          counter: 52,
          uuid: 'abc-052',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          id: 153,
          counter: 53,
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
  });

  describe('getTotalNumChildren', () => {
    let wrapper;
    beforeEach(() => {
      wrapper = shallow(<HookTest />);
      wrapper.find('#test').prop('addEvents')(eventsList);
    });

    test('should get basic number of children', () => {
      expect(
        wrapper.find('#test').prop('getTotalNumChildren')('abc-002')
      ).toEqual(3);
    });

    test('should get total number of nested children', () => {
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
      callbacks.fetchNumEvents.mockImplementation((counter) => {
        const children = {
          1: 28,
          2: 3,
          6: 23,
        };
        return children[counter];
      });
      const wrapper = mount(<HookTest {...callbacks} />);
      wrapper.update();
      await act(async () => {
        wrapper.find('#test').prop('addEvents')(eventsList);
        wrapper.find('#test').prop('addEvents')([
          {
            id: 130,
            counter: 30,
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
      callbacks.fetchNumEvents.mockImplementation((counter) => {
        const children = {
          1: 85,
          2: 66,
          69: 17,
        };
        return children[counter];
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
      callbacks.fetchNumEvents.mockImplementation(
        (counter) =>
          ({
            1: 30,
          }[counter])
      );
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 102,
            counter: 2,
            uuid: 'abc-002',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 103,
            counter: 3,
            uuid: 'abc-003',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 120,
            counter: 20,
            uuid: 'abc-020',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 121,
            counter: 21,
            uuid: 'abc-021',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 122,
            counter: 22,
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
      callbacks.fetchNumEvents.mockImplementation(
        (counter) =>
          ({
            1: 30,
          }[counter])
      );
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 120,
            counter: 20,
            uuid: 'abc-020',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 121,
            counter: 21,
            uuid: 'abc-021',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 122,
            counter: 22,
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
      callbacks.fetchNumEvents.mockImplementation(
        (counter) =>
          ({
            1: 30,
          }[counter])
      );
      const wrapper = mount(<HookTest {...callbacks} />);
      await act(async () => {
        wrapper.find('#test').prop('addEvents')([
          eventsList[0],
          {
            id: 109,
            counter: 9,
            uuid: 'abc-009',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 110,
            counter: 10,
            uuid: 'abc-010',
            event_level: 1,
            parent_uuid: 'abc-001',
          },
          {
            id: 111,
            counter: 11,
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
