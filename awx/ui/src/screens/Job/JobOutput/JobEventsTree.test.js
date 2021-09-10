import JobEventsTree from './JobEventsTree';

describe('JobEventsTree', () => {
  const eventsList = [
    { counter: 1, uuid: 'abc-001', event_level: 0 },
    { counter: 2, uuid: 'abc-002', event_level: 1, parent_uuid: 'abc-001' },
    { counter: 3, uuid: 'abc-003', event_level: 2, parent_uuid: 'abc-002' },
    { counter: 4, uuid: 'abc-004', event_level: 2, parent_uuid: 'abc-002' },
    { counter: 5, uuid: 'abc-005', event_level: 2, parent_uuid: 'abc-002' },
    { counter: 6, uuid: 'abc-006', event_level: 1, parent_uuid: 'abc-001' },
    { counter: 7, uuid: 'abc-007', event_level: 2, parent_uuid: 'abc-006' },
    { counter: 8, uuid: 'abc-008', event_level: 2, parent_uuid: 'abc-006' },
    { counter: 9, uuid: 'abc-009', event_level: 2, parent_uuid: 'abc-006' },
  ];

  describe('addEvents', () => {
    test('should build initial tree', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      expect(tree.getAllEvents()).toEqual({
        1: eventsList[0],
        2: eventsList[1],
        3: eventsList[2],
        4: eventsList[3],
        5: eventsList[4],
        6: eventsList[5],
        7: eventsList[6],
        8: eventsList[7],
        9: eventsList[8],
      });
      expect(tree.getEventTree()).toEqual([
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

    test('should append new events', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const newEvents = [
        {
          counter: 10,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-006',
        },
        {
          counter: 11,
          uuid: 'abc-011',
          event_level: 1,
          parent_uuid: 'abc-001',
        },
        { counter: 12, uuid: 'abc-012', event_level: 0, parent_uuid: '' },
      ];
      tree.addEvents(newEvents);

      expect(tree.getAllEvents()).toEqual({
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
      expect(tree.getEventTree()).toEqual([
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

    test('should not duplicate events in events tree', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      tree.addEvents(eventsList);

      expect(tree.getAllEvents()).toEqual({
        1: eventsList[0],
        2: eventsList[1],
        3: eventsList[2],
        4: eventsList[3],
        5: eventsList[4],
        6: eventsList[5],
        7: eventsList[6],
        8: eventsList[7],
        9: eventsList[8],
      });
      expect(tree.getEventTree()).toEqual([
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

    test('should fetch parent for events with missing parent', () => {
      const fetchParent = jest.fn();
      const tree = new JobEventsTree({}, fetchParent);
      tree.addEvents(eventsList);

      const newEvents = [
        {
          counter: 12,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      tree.addEvents(newEvents);

      expect(fetchParent).toHaveBeenCalledWith('abc-010');
    });

    test('should batch parent fetches by uuid', () => {
      const fetchParent = jest.fn();
      const tree = new JobEventsTree({}, fetchParent);
      tree.addEvents(eventsList);

      const newEvents = [
        {
          counter: 12,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
        {
          counter: 13,
          uuid: 'abc-013',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      tree.addEvents(newEvents);

      expect(fetchParent).toHaveBeenCalledTimes(1);
      expect(fetchParent).toHaveBeenCalledWith('abc-010');
    });

    test('should fetch multiple parent fetches by uuid', () => {
      const fetchParent = jest.fn();
      const tree = new JobEventsTree({}, fetchParent);
      tree.addEvents(eventsList);

      const newEvents = [
        {
          counter: 14,
          uuid: 'abc-014',
          event_level: 2,
          parent_uuid: 'abc-012',
        },
        {
          counter: 15,
          uuid: 'abc-015',
          event_level: 1,
          parent_uuid: 'abc-011',
        },
      ];
      tree.addEvents(newEvents);

      expect(fetchParent).toHaveBeenCalledTimes(2);
      expect(fetchParent).toHaveBeenCalledWith('abc-012');
      expect(fetchParent).toHaveBeenCalledWith('abc-011');
    });

    test('should set eventsWithoutParents while fetching parent events', () => {
      const tree = new JobEventsTree({}, jest.fn());
      tree.addEvents(eventsList);

      const newEvents = [
        {
          counter: 12,
          uuid: 'abc-012',
          event_level: 2,
          parent_uuid: 'abc-010',
        },
      ];
      tree.addEvents(newEvents);

      expect(tree.getEventsWithoutParents()).toEqual({
        'abc-010': [newEvents[0]],
      });
      expect(tree.getNodeByUuid('abc-010')).toEqual(null);
    });

    test('should check for eventsWithoutParents belonging to new nodes', () => {
      const tree = new JobEventsTree(
        {
          eventsWithoutParents: {
            'abc-010': [
              {
                counter: 12,
                uuid: 'abc-012',
                event_level: 1,
                parent_uuid: 'abc-010',
              },
            ],
          },
        },
        jest.fn()
      );

      const parentEvent = {
        counter: 10,
        uuid: 'abc-010',
        event_level: 0,
        parent_uuid: '',
      };
      tree.addEvents([parentEvent]);

      expect(tree.getEventTree()).toEqual([
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
      expect(tree.getEventsWithoutParents()).toEqual({});
    });

    test('should fetch parent of parent and compile them together', () => {
      const fetchParent = jest.fn();
      const tree = new JobEventsTree({}, fetchParent);

      const event3 = {
        counter: 3,
        uuid: 'abc-003',
        event_level: 2,
        parent_uuid: 'abc-002',
      };
      tree.addEvents([event3]);
      expect(fetchParent).toHaveBeenCalledWith('abc-002');

      const event2 = {
        counter: 2,
        uuid: 'abc-002',
        event_level: 1,
        parent_uuid: 'abc-001',
      };
      tree.addEvents([event2]);
      expect(fetchParent).toHaveBeenCalledWith('abc-001');
      expect(tree.getAllEvents()).toEqual({});
      expect(tree.getEventTree()).toEqual([]);
      expect(tree.getEventsWithoutParents()).toEqual({
        'abc-001': [event2],
        'abc-002': [event3],
      });

      const event1 = {
        counter: 1,
        uuid: 'abc-001',
        event_level: 0,
        parent_uuid: '',
      };
      tree.addEvents([event1]);
      expect(tree.getAllEvents()).toEqual({
        1: event1,
        2: event2,
        3: event3,
      });
      expect(tree.getEventTree()).toEqual([
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
      expect(tree.getEventsWithoutParents()).toEqual({});
    });

    test('should add root level node in middle of array', () => {
      const tree = new JobEventsTree();

      const events = [
        {
          counter: 1,
          uuid: 'abc-001',
          event_level: 0,
          parent_uuid: '',
        },
        {
          counter: 2,
          uuid: 'abc-002',
          event_level: 0,
          parent_uuid: '',
        },
        {
          counter: 3,
          uuid: 'abc-003',
          event_level: 0,
          parent_uuid: '',
        },
      ];
      tree.addEvents([events[0]]);
      tree.addEvents([events[2]]);
      tree.addEvents([events[1]]);

      const eventsTree = tree.getEventTree();
      expect(eventsTree[0].eventIndex).toEqual(1);
      expect(eventsTree[1].eventIndex).toEqual(2);
      expect(eventsTree[2].eventIndex).toEqual(3);
    });

    test('should add child nodes in middle of array', () => {
      const tree = new JobEventsTree();
      tree.addEvents([...eventsList.slice(0, 3), ...eventsList.slice(4)]);

      tree.addEvents([eventsList[3]]);

      expect(tree.getEventTree()).toEqual([
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

    // TODO: how/when are child counts wrong
  });

  describe('getNodeByUuid', () => {
    test('should get a root node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-001');
      expect(node.eventIndex).toEqual(1);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(2);
    });

    test('should get 2nd level node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-002');
      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(3);
    });

    test('should get 3rd level node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-008');
      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(0);
    });

    test('should return null if node not found', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-028');
      expect(node).toEqual(null);
    });
  });

  describe('toggleNodeIsCollapsed', () => {
    test('should collapse node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      tree.toggleNodeIsCollapsed('abc-001');

      const node = tree.getNodeByUuid('abc-001');
      expect(node.isCollapsed).toBe(true);
    });

    test('should expand node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      tree.toggleNodeIsCollapsed('abc-001');
      tree.toggleNodeIsCollapsed('abc-001');

      const node = tree.getNodeForRow(1);
      expect(node.isCollapsed).toBe(false);
    });

    test.skip('should update total row count', () => {});
  });

  describe('getNodeForRow', () => {
    test('should get root node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeForRow(0);
      expect(node.eventIndex).toEqual(1);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(2);
    });

    test('should get 2nd level node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeForRow(1);
      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(3);
    });

    test('should get 3rd level node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeForRow(7);
      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toEqual(false);
      expect(node.children).toHaveLength(0);
    });

    test('should get a second root-level node', () => {
      const tree = new JobEventsTree();
      const lastNode = { counter: 10, uuid: 'abc-010', event_level: 0 };
      tree.addEvents([...eventsList, lastNode]);

      const node = tree.getNodeForRow(9);
      expect(node).toEqual({
        eventIndex: 10,
        isCollapsed: false,
        children: [],
      });
    });

    test('should return null if no node matches index', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeForRow(10);
      expect(node).toEqual(null);
    });

    test('should return collapsed node', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);
      tree.toggleNodeIsCollapsed('abc-002');

      const node = tree.getNodeForRow(1);

      expect(node.eventIndex).toEqual(2);
      expect(node.isCollapsed).toBe(true);
    });

    test('should skip nodes with collapsed parent', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);
      tree.toggleNodeIsCollapsed('abc-002');

      const node = tree.getNodeForRow(2);
      expect(node.eventIndex).toEqual(6);
      expect(node.isCollapsed).toBe(false);

      const node2 = tree.getNodeForRow(4);
      expect(node2.eventIndex).toEqual(8);
      expect(node2.isCollapsed).toBe(false);
    });

    test('should skip deeply-nested collapsed nodes', () => {
      const tree = new JobEventsTree();
      tree.addEvents([
        { counter: 1, uuid: 'abc-001', event_level: 0 },
        { counter: 2, uuid: 'abc-002', event_level: 1, parent_uuid: 'abc-001' },
        { counter: 3, uuid: 'abc-003', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 4, uuid: 'abc-004', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 5, uuid: 'abc-005', event_level: 3, parent_uuid: 'abc-004' },
        { counter: 6, uuid: 'abc-006', event_level: 3, parent_uuid: 'abc-004' },
        { counter: 7, uuid: 'abc-007', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 8, uuid: 'abc-008', event_level: 1, parent_uuid: 'abc-001' },
        { counter: 9, uuid: 'abc-009', event_level: 2, parent_uuid: 'abc-008' },
        {
          counter: 10,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
      ]);
      tree.toggleNodeIsCollapsed('abc-004');

      const node = tree.getNodeForRow(5);
      expect(node.eventIndex).toEqual(8);
      expect(node.isCollapsed).toBe(false);
    });

    test('should skip full sub-tree of collapsed node', () => {
      const tree = new JobEventsTree();
      tree.addEvents([
        { counter: 1, uuid: 'abc-001', event_level: 0 },
        { counter: 2, uuid: 'abc-002', event_level: 1, parent_uuid: 'abc-001' },
        { counter: 3, uuid: 'abc-003', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 4, uuid: 'abc-004', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 5, uuid: 'abc-005', event_level: 3, parent_uuid: 'abc-004' },
        { counter: 6, uuid: 'abc-006', event_level: 3, parent_uuid: 'abc-004' },
        { counter: 7, uuid: 'abc-007', event_level: 2, parent_uuid: 'abc-002' },
        { counter: 8, uuid: 'abc-008', event_level: 1, parent_uuid: 'abc-001' },
        { counter: 9, uuid: 'abc-009', event_level: 2, parent_uuid: 'abc-008' },
        {
          counter: 10,
          uuid: 'abc-010',
          event_level: 2,
          parent_uuid: 'abc-008',
        },
      ]);
      tree.toggleNodeIsCollapsed('abc-002');

      const node = tree.getNodeForRow(3);
      expect(node.eventIndex).toEqual(9);
      expect(node.isCollapsed).toBe(false);
    });

    // missing node
    // loading node?
  });

  describe('getTotalNumChildren', () => {
    test('should get basic number of children', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-002');

      expect(tree.getTotalNumChildren(node)).toEqual(3);
    });

    test('should get total number of nested children', () => {
      const tree = new JobEventsTree();
      tree.addEvents(eventsList);

      const node = tree.getNodeByUuid('abc-001');

      expect(tree.getTotalNumChildren(node)).toEqual(8);
    });
  });
});
