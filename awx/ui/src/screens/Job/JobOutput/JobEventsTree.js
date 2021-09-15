import { useReducer } from 'react';

const initialState = {
  // array of root level nodes (event_level: 0)
  tree: [],
  // all events indexed by counter value
  events: {},
  // lookup info (counter value & location in tree) indexed by uuid
  uuidMap: {},
  // events with parent events that aren't yet loaded.
  // arrays indexed by parent uuid
  eventsWithoutParents: {},
};
export const ADD_EVENTS = 'ADD_EVENTS';
export const TOGGLE_NODE_COLLAPSED = 'TOGGLE_NODE_COLLAPSED';

export default function useJobEventsTree(fetchEventByUuid) {
  const reducer = jobEventsReducer({ fetchEventByUuid });
  const [state, dispatch] = useReducer(reducer, initialState);

  // todo useCallback() these?
  return {
    addEvents: (events) => dispatch({ type: ADD_EVENTS, events }),
    getNodeByUuid: (uuid) => getNodeByUuid(state, uuid),
    toggleNodeIsCollapsed: (uuid) =>
      dispatch({ type: TOGGLE_NODE_COLLAPSED, uuid }),
    getNodeForRow: (rowIndex) => getNodeForRow(state, rowIndex),
    getTotalNumChildren: (uuid) => {
      const node = getNodeByUuid(state, uuid);
      return getTotalNumChildren(node);
    },
  };
}

export function jobEventsReducer(callbacks) {
  return (state, action) => {
    switch (action.type) {
      case ADD_EVENTS:
        return addEvents(state, action.events);
      case TOGGLE_NODE_COLLAPSED:
        return toggleNodeIsCollapsed(state, action.uuid);
      default:
        throw new Error(`Unrecognized action: ${action.type}`);
    }
  };

  function addEvents(origState, newEvents) {
    let state = { ...origState, events: { ...origState.events } };
    const parentsToFetch = new Set();
    newEvents.forEach((event) => {
      // todo normalize?
      const eventIndex = event.counter;
      if (state.events[eventIndex]) {
        state.events[eventIndex] = event;
        state = _gatherEventsForNewParent(state, event.uuid);
        return;
      }
      if (event.event_level === 0) {
        state = _addRootLevelEvent(state, event);
        state.events[eventIndex] = event;
        return;
      }

      let isParentFound;
      [state, isParentFound] = _addNestedLevelEvent(state, event);
      if (isParentFound) {
        state.events[eventIndex] = event;
      } else {
        parentsToFetch.add(event.parent_uuid);
        state = _addEventWithoutParent(state, event);
      }
    });

    // TODO: update callback to accept array of uuids/do it in 1 request
    parentsToFetch.forEach((uuid) => callbacks.fetchEventByUuid(uuid));

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
    let length;
    if (index === -1) {
      length = updatedTree.push(newNode);
    } else {
      updatedTree.splice(index, 0, newNode);
      length = updatedTree.length;
    }
    return _gatherEventsForNewParent(
      {
        ...state,
        tree: updatedTree,
        uuidMap: {
          ...state.uuidMap,
          [event.uuid]: {
            index: eventIndex,
            treePath: [length - 1],
          },
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
      (node) => node.eventIndex > eventIndex
    );
    let length;
    // TODO update Parent correctly in tree/setTree ***
    if (index === -1) {
      length = parent.children.push(newNode);
    } else {
      parent.children.splice(index, 0, newNode);
      length = parent.children.length;
    }
    const { treePath: parentTreePath } = state.uuidMap[event.parent_uuid];
    state.uuidMap = {
      ...state.uuidMap,
      [event.uuid]: {
        index: eventIndex,
        treePath: [...parentTreePath, length - 1],
      },
    };
    state = _gatherEventsForNewParent(state, event.uuid);

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
}

function getEventForRow(state, rowIndex) {
  const node = getNodeForRow(rowIndex);
  if (!node) {
    return null;
  }
  return {
    node,
    event: state.events[node.eventIndex],
  };
}

function getNodeForRow(state, rowToFind) {
  const [node] = _getNodeForRow(state, rowToFind + 1, state.tree);
  return node;
}

// TODO don't depend on eventIndex
function _getNodeForRow(state, rowToFind, nodes) {
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    const nextNode = nodes[i + 1] || {};
    if (state.events[node.eventIndex].counter === rowToFind) {
      return [node, rowToFind];
    }
    if (node.isCollapsed) {
      rowToFind += getTotalNumChildren(node, nextNode);
      continue;
    }
    if (!nextNode.eventIndex || nextNode.eventIndex > rowToFind) {
      const [found, newRowToFind] = _getNodeForRow(
        state,
        rowToFind,
        node.children
      );
      if (found) {
        return [found, newRowToFind];
      }
      rowToFind = newRowToFind;
    }
  }
  return [null, rowToFind];
}

// TODO: move; this will need access to dispatch :(
function getTotalNumChildren(node, siblingNode = null) {
  // GOTCHA: requires no un-loaded siblings between node & siblingNode
  if (siblingNode?.eventIndex) {
    return siblingNode.eventIndex - node.eventIndex - 1;
  }
  let sum = node.children.length;
  node.children.forEach((child, i) => {
    sum += getTotalNumChildren(child, node.children[i + 1]);
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
  const tree = [...state.tree];
  let arr = tree;
  const { treePath } = state.uuidMap[uuid];
  for (let i = 0; i < treePath.length; i++) {
    const index = treePath[i];
    const children = [...arr[index].children];
    let node = arr[index];
    if (i === treePath.length - 1) {
      node = update(node);
    }
    arr[index] = {
      ...node,
      children,
    };
    arr = children;
  }

  return {
    ...state,
    tree,
  };
}

function getNodeByUuid(state, uuid) {
  if (!state.uuidMap[uuid]) {
    return null;
  }
  const { treePath } = state.uuidMap[uuid];
  let arr = state.tree;
  let lastNode;
  for (let i = 0; i < treePath.length; i++) {
    const index = treePath[i];
    lastNode = arr[index];
    arr = arr[index].children;
  }
  return lastNode;
}
