import { useState, useEffect, useReducer } from 'react';

const initialState = {
  // array of root level nodes (no parent_uuid)
  tree: [],
  // all events indexed by counter value
  events: {},
  // counter value indexed by uuid
  uuidMap: {},
  // events with parent events that aren't yet loaded.
  // arrays indexed by parent uuid
  eventsWithoutParents: {},
};
export const ADD_EVENTS = 'ADD_EVENTS';
export const TOGGLE_NODE_COLLAPSED = 'TOGGLE_NODE_COLLAPSED';
export const SET_EVENT_NUM_CHILDREN = 'SET_EVENT_NUM_CHILDREN';
export const CLEAR_EVENTS = 'CLEAR_EVENTS';
export const REBUILD_TREE = 'REBUILD_TREE';

export default function useJobEvents(callbacks, isFlatMode) {
  const [actionQueue, setActionQueue] = useState([]);
  const enqueueAction = (action) => {
    setActionQueue((queue) => queue.concat(action));
  };
  const reducer = jobEventsReducer(callbacks, isFlatMode, enqueueAction);
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    setActionQueue((queue) => {
      const action = queue[0];
      if (!action) {
        return queue;
      }
      try {
        dispatch(action);
      } catch (e) {
        console.error(e); // eslint-disable-line no-console
      }
      return queue.slice(1);
    });
  }, [actionQueue]);

  return {
    addEvents: (events) => dispatch({ type: ADD_EVENTS, events }),
    getNodeByUuid: (uuid) => getNodeByUuid(state, uuid),
    toggleNodeIsCollapsed: (uuid) =>
      dispatch({ type: TOGGLE_NODE_COLLAPSED, uuid }),
    getEventForRow: (rowIndex) => getEventForRow(state, rowIndex),
    getNodeForRow: (rowIndex) => getNodeForRow(state, rowIndex),
    getTotalNumChildren: (uuid) => {
      const node = getNodeByUuid(state, uuid);
      return getTotalNumChildren(node);
    },
    getNumCollapsedEvents: () =>
      state.tree.reduce((sum, node) => sum + getNumCollapsedChildren(node), 0),
    getCounterForRow: (rowIndex) => getCounterForRow(state, rowIndex),
    getEvent: (eventIndex) => getEvent(state, eventIndex),
    clearLoadedEvents: () => dispatch({ type: CLEAR_EVENTS }),
    rebuildEventsTree: () => dispatch({ type: REBUILD_TREE }),
  };
}

export function jobEventsReducer(callbacks, isFlatMode, enqueueAction) {
  return (state, action) => {
    switch (action.type) {
      case ADD_EVENTS:
        return addEvents(state, action.events);
      case TOGGLE_NODE_COLLAPSED:
        return toggleNodeIsCollapsed(state, action.uuid);
      case SET_EVENT_NUM_CHILDREN:
        return setEventNumChildren(state, action.uuid, action.numChildren);
      case CLEAR_EVENTS:
        return initialState;
      case REBUILD_TREE:
        return rebuildTree(state);
      default:
        throw new Error(`Unrecognized action: ${action.type}`);
    }
  };

  function addEvents(origState, newEvents) {
    let state = {
      ...origState,
      events: { ...origState.events },
      tree: [...origState.tree],
    };
    const parentsToFetch = {};
    newEvents.forEach((event) => {
      if (
        typeof event.rowNumber !== 'number' ||
        Number.isNaN(event.rowNumber)
      ) {
        throw new Error('Cannot add event; missing rowNumber');
      }
      const eventIndex = event.counter;
      if (state.events[eventIndex]) {
        state.events[eventIndex] = event;
        state = _gatherEventsForNewParent(state, event.uuid);
        return;
      }
      if (!event.parent_uuid || isFlatMode) {
        state = _addRootLevelEvent(state, event);
        return;
      }

      let isParentFound;
      [state, isParentFound] = _addNestedLevelEvent(state, event);
      if (!isParentFound) {
        parentsToFetch[event.parent_uuid] = {
          childCounter: event.counter,
          childRowNumber: event.rowNumber,
        };
        state = _addEventWithoutParent(state, event);
      }
    });

    Object.keys(parentsToFetch).forEach(async (uuid) => {
      const { childCounter, childRowNumber } = parentsToFetch[uuid];
      const parent = await callbacks.fetchEventByUuid(uuid);
      const numPrevSiblings = await callbacks.fetchNumEvents(
        parent.counter,
        childCounter
      );
      parent.rowNumber = childRowNumber - numPrevSiblings - 1;
      enqueueAction({
        type: ADD_EVENTS,
        events: [parent],
      });
    });

    return state;
  }

  function _addRootLevelEvent(state, event) {
    const eventIndex = event.counter;
    const newNode = {
      eventIndex,
      isCollapsed: false,
      children: [],
    };
    const index = state.tree.findIndex((node) => node.eventIndex > eventIndex);
    const updatedTree = [...state.tree];
    if (index === -1) {
      updatedTree.push(newNode);
    } else {
      updatedTree.splice(index, 0, newNode);
    }
    return _gatherEventsForNewParent(
      {
        ...state,
        events: { ...state.events, [eventIndex]: event },
        tree: updatedTree,
        uuidMap: {
          ...state.uuidMap,
          [event.uuid]: eventIndex,
        },
      },
      event.uuid
    );
  }

  function _addNestedLevelEvent(state, event) {
    const eventIndex = event.counter;
    const parent = getNodeByUuid(state, event.parent_uuid);
    if (!parent) {
      return [state, false];
    }
    const newNode = {
      eventIndex,
      isCollapsed: false,
      children: [],
    };
    const index = parent.children.findIndex(
      (node) => node.eventIndex >= eventIndex
    );
    const length = parent.children.length + 1;
    if (index === -1) {
      state = updateNodeByUuid(state, event.parent_uuid, (node) => {
        node.children.push(newNode);
        return node;
      });
    } else {
      state = updateNodeByUuid(state, event.parent_uuid, (node) => {
        node.children.splice(index, 0, newNode);
        return node;
      });
    }
    state = _gatherEventsForNewParent(
      {
        ...state,
        events: {
          ...state.events,
          [eventIndex]: event,
        },
        uuidMap: {
          ...state.uuidMap,
          [event.uuid]: eventIndex,
        },
      },
      event.uuid
    );
    if (length === 1) {
      _fetchNumChildren(state, parent);
    }

    return [state, true];
  }

  function _addEventWithoutParent(state, event) {
    const parentUuid = event.parent_uuid;
    let eventsList;
    if (!state.eventsWithoutParents[parentUuid]) {
      eventsList = [event];
    } else {
      eventsList = state.eventsWithoutParents[parentUuid].concat(event);
    }

    return {
      ...state,
      eventsWithoutParents: {
        ...state.eventsWithoutParents,
        [parentUuid]: eventsList,
      },
    };
  }

  async function _fetchNumChildren(state, node) {
    const event = state.events[node.eventIndex];
    if (!event) {
      throw new Error(
        `Cannot fetch numChildren; event ${node.eventIndex} not found`
      );
    }
    const sibling = await _getNextSibling(state, event);
    const numChildren = await callbacks.fetchNumEvents(
      event.counter,
      sibling?.counter
    );
    enqueueAction({
      type: SET_EVENT_NUM_CHILDREN,
      uuid: event.uuid,
      numChildren,
    });
    if (sibling) {
      sibling.rowNumber = event.rowNumber + numChildren + 1;
      enqueueAction({
        type: ADD_EVENTS,
        events: [sibling],
      });
    }
  }

  async function _getNextSibling(state, event) {
    if (!event.parent_uuid) {
      return callbacks.fetchNextRootNode(event.counter);
    }
    const parentNode = getNodeByUuid(state, event.parent_uuid);
    const parent = state.events[parentNode.eventIndex];
    const sibling = await callbacks.fetchNextSibling(parent.id, event.counter);
    if (!sibling) {
      return _getNextSibling(state, parent);
    }
    return sibling;
  }

  function _gatherEventsForNewParent(state, parentUuid) {
    if (!state.eventsWithoutParents[parentUuid]) {
      return state;
    }

    const { [parentUuid]: newEvents, ...remaining } =
      state.eventsWithoutParents;
    return addEvents(
      {
        ...state,
        eventsWithoutParents: remaining,
      },
      newEvents
    );
  }

  function rebuildTree(state) {
    const events = Object.values(state.events);
    return addEvents(initialState, events);
  }
}

function getEventForRow(state, rowIndex) {
  const { node } = _getNodeForRow(state, rowIndex, state.tree);
  if (node) {
    return {
      node,
      event: state.events[node.eventIndex],
    };
  }
  return null;
}

function getNodeForRow(state, rowToFind) {
  const { node } = _getNodeForRow(state, rowToFind, state.tree);
  return node;
}

function getCounterForRow(state, rowToFind) {
  const { node, expectedCounter } = _getNodeForRow(
    state,
    rowToFind,
    state.tree
  );

  if (node) {
    const event = state.events[node.eventIndex];
    return event.counter;
  }
  return expectedCounter;
}

function _getNodeForRow(state, rowToFind, nodes) {
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    const event = state.events[node.eventIndex];
    if (event.rowNumber === rowToFind) {
      return { node };
    }
    const totalNodeDescendants = getTotalNumChildren(node);
    const numCollapsedChildren = getNumCollapsedChildren(node);
    const nodeChildren = totalNodeDescendants - numCollapsedChildren;
    if (event.rowNumber + nodeChildren >= rowToFind) {
      // requested row is in children/descendants
      return _getNodeInChildren(state, node, rowToFind);
    }
    rowToFind += numCollapsedChildren;

    const nextNode = nodes[i + 1];
    if (!nextNode) {
      continue;
    }
    const nextEvent = state.events[nextNode.eventIndex];
    const lastChild = _getLastDescendantNode([node]);
    if (nextEvent.rowNumber > rowToFind) {
      // requested row is not loaded; return best guess at counter number
      const lastChildEvent = state.events[lastChild.eventIndex];
      const rowDiff = rowToFind - lastChildEvent.rowNumber;
      return {
        node: null,
        expectedCounter: lastChild.eventIndex + rowDiff,
      };
    }
  }

  const lastDescendant = _getLastDescendantNode(nodes);
  if (!lastDescendant) {
    return { node: null, expectedCounter: rowToFind };
  }

  const lastDescendantEvent = state.events[lastDescendant.eventIndex];
  const rowDiff = rowToFind - lastDescendantEvent.rowNumber;
  return {
    node: null,
    expectedCounter: lastDescendant.eventIndex + rowDiff,
  };
}

function _getNodeInChildren(state, node, rowToFind) {
  const event = state.events[node.eventIndex];
  const firstChild = state.events[node.children[0].eventIndex];
  if (rowToFind < firstChild.rowNumber) {
    const rowDiff = rowToFind - event.rowNumber;
    return {
      node: null,
      expectedCounter: event.counter + rowDiff,
    };
  }
  return _getNodeForRow(state, rowToFind, node.children);
}

function _getLastDescendantNode(nodes) {
  let lastDescendant = nodes[nodes.length - 1];
  let children = lastDescendant?.children || [];
  while (children.length) {
    lastDescendant = children[children.length - 1];
    children = lastDescendant.children;
  }
  return lastDescendant;
}

function getTotalNumChildren(node) {
  if (typeof node.numChildren !== 'undefined') {
    return node.numChildren;
  }

  let estimatedNumChildren = node.children.length;
  node.children.forEach((child) => {
    estimatedNumChildren += getTotalNumChildren(child);
  });
  return estimatedNumChildren;
}

function getNumCollapsedChildren(node) {
  if (node.isCollapsed) {
    return getTotalNumChildren(node);
  }

  let sum = 0;
  node.children.forEach((child) => {
    sum += getNumCollapsedChildren(child);
  });
  return sum;
}

function toggleNodeIsCollapsed(state, eventUuid) {
  return updateNodeByUuid(state, eventUuid, (node) => ({
    ...node,
    isCollapsed: !node.isCollapsed,
  }));
}

function updateNodeByUuid(state, uuid, update) {
  if (!state.uuidMap[uuid]) {
    throw new Error(`Cannot update node; Event UUID not found ${uuid}`);
  }
  const index = state.uuidMap[uuid];
  return {
    ...state,
    tree: _updateNodeByIndex(index, state.tree, update),
  };
}

function _updateNodeByIndex(target, nodeArray, update) {
  const nextIndex = nodeArray.findIndex((node) => node.eventIndex > target);
  const targetIndex = nextIndex === -1 ? nodeArray.length - 1 : nextIndex - 1;
  let updatedNode;
  if (nodeArray[targetIndex].eventIndex === target) {
    updatedNode = update({
      ...nodeArray[targetIndex],
      children: [...nodeArray[targetIndex].children],
    });
  } else {
    updatedNode = {
      ...nodeArray[targetIndex],
      children: _updateNodeByIndex(
        target,
        nodeArray[targetIndex].children,
        update
      ),
    };
  }
  return [
    ...nodeArray.slice(0, targetIndex),
    updatedNode,
    ...nodeArray.slice(targetIndex + 1),
  ];
}

function getNodeByUuid(state, uuid) {
  if (!state.uuidMap[uuid]) {
    return null;
  }

  const index = state.uuidMap[uuid];
  return _getNodeByIndex(state.tree, index);
}

function _getNodeByIndex(arr, index) {
  if (!arr.length) {
    return null;
  }
  const i = arr.findIndex((node) => node.eventIndex >= index);
  if (i === -1) {
    return _getNodeByIndex(arr[arr.length - 1].children, index);
  }
  if (arr[i].eventIndex === index) {
    return arr[i];
  }
  if (!arr[i - 1]) {
    return null;
  }
  return _getNodeByIndex(arr[i - 1].children, index);
}

function setEventNumChildren(state, uuid, numChildren) {
  if (!state.uuidMap[uuid]) {
    return state;
  }
  return updateNodeByUuid(state, uuid, (node) => ({
    ...node,
    numChildren,
  }));
}

function getEvent(state, eventIndex) {
  const event = state.events[eventIndex];
  if (event) {
    return event;
  }

  return null;
}
