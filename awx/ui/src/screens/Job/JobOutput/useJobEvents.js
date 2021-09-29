import { useState, useEffect, useReducer } from 'react';

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
export const SET_EVENT_NUM_CHILDREN = 'SET_EVENT_NUM_CHILDREN';

export default function useJobEvents(callbacks) {
  const [actionQueue, setActionQueue] = useState([]);
  const enqueueAction = (action) => {
    setActionQueue((queue) => queue.concat(action));
  };
  const reducer = jobEventsReducer(callbacks, enqueueAction);
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    setActionQueue((queue) => {
      const action = queue[0];
      if (!action) {
        return queue;
      }
      dispatch(action);
      return queue.slice(1);
    });
  }, [actionQueue]);

  window.getEventForRow = (index) => {
    const counter = getCounterForRow(state, index);
    return [getEventForRow(state, index), counter, state.events[counter]];
  };

  // todo useCallback() these?
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
    getEvent: (rowIndex) => state.events[rowIndex] || null,
  };
}

export function jobEventsReducer(callbacks, enqueueAction) {
  return (state, action) => {
    switch (action.type) {
      case ADD_EVENTS:
        return addEvents(state, action.events);
      case TOGGLE_NODE_COLLAPSED:
        return toggleNodeIsCollapsed(state, action.uuid);
      case SET_EVENT_NUM_CHILDREN:
        return setEventNumChildren(state, action.uuid, action.numChildren);
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
    const parentsToFetch = new Set();
    newEvents.forEach((event) => {
      // todo normalize?
      const eventIndex = event.counter;
      if (state.events[eventIndex]) {
        state.events[eventIndex] = event;
        state = _gatherEventsForNewParent(state, event.uuid);
        return;
      }
      if (event.event_level === 0 || !event.parent_uuid) {
        state = _addRootLevelEvent(state, event);
        return;
      }

      let isParentFound;
      [state, isParentFound] = _addNestedLevelEvent(state, event);
      if (!isParentFound) {
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
        events: {
          ...state.events,
          [eventIndex]: event,
        },
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
    // TODO: don't duplicate event if already in children
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
    const { treePath: parentTreePath } = state.uuidMap[event.parent_uuid];
    state = _gatherEventsForNewParent(
      {
        ...state,
        events: {
          ...state.events,
          [eventIndex]: event,
        },
        uuidMap: {
          ...state.uuidMap,
          [event.uuid]: {
            index: eventIndex,
            treePath: [...parentTreePath, length - 1],
          },
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
}

function getEventForRow(state, rowIndex) {
  const node = getNodeForRow(state, rowIndex);
  if (!node) {
    return null;
  }
  return {
    node,
    event: state.events[node.eventIndex],
  };
}

function getNodeForRow(state, rowToFind) {
  const { node } = _getNodeForRow(state, rowToFind + 1, state.tree);
  return node;
}

function _getNodeForRow(state, rowToFind, nodes) {
  let remainingCount = rowToFind;
  for (let i = 0; i < nodes.length; i++) {
    const node = nodes[i];
    if (window.debugMode) console.log('Visiting', { node, remainingCount });
    if (remainingCount === 1) {
      if (window.debugMode) console.log('a', node);
      return { node };
    }
    remainingCount--;
    if (remainingCount < 1) {
      // looking for a node that hasn't been loaded yet
      if (window.debugMode) console.log('b', node);
      return { node: null };
    }
    const totalNodeDescendants = getTotalNumChildren(node);
    const nodeChildren = totalNodeDescendants - getNumCollapsedChildren(node);
    if (window.debugMode) console.log({ nodeChildren, remainingCount });
    if (nodeChildren >= remainingCount) {
      if (node.children[0].eventIndex > node.eventIndex + remainingCount) {
        return {
          node: null,
          expectedCounter: node.eventIndex + remainingCount,
        };
      }
      const counterGap = node.children[0].eventIndex - (node.eventIndex + 1);
      if (remainingCount > counterGap) {
        remainingCount -= counterGap;
      }
      return _getNodeForRow(state, remainingCount, node.children);
      // const result = _getNodeForRow(state, remainingCount, node.children);
      // if (result.parentNode) {
      //   if (window.debugMode) console.log('c', node);
      //   return result;
      // }
      // if (node.isCollapsed) {
      //   if (window.debugMode) console.log('d', node);
      //   return result;
      // }
      // if (window.debugMode) console.log('e', result, node, remainingCount);
      // return {
      //   ...result,
      //   parentNode: node,
      //   parentOffset: remainingCount,
      // };
    }
    remainingCount -= nodeChildren;

    const nextNode = nodes[i + 1];
    if (nextNode) {
      const lastChildCounter = node.eventIndex + totalNodeDescendants;
      const counterGap = nextNode.eventIndex - (lastChildCounter + 1);
      if (remainingCount - counterGap < 1) {
        return {
          node: null,
          expectedCounter: lastChildCounter + remainingCount,
        };
      }
      remainingCount -= counterGap;
    }
  }
  let lastDescendant = nodes[nodes.length - 1];
  let children = lastDescendant?.children || [];
  while (children.length) {
    lastDescendant = children[children.length - 1];
    children = lastDescendant.children;
  }
  if (!lastDescendant) {
    console.log('NO LAST NODE FOUND');
    return { node: null, remainingCount };
  }

  const lastEvent = state.events[lastDescendant.eventIndex];
  if (window.debugMode) {
    console.log({ last: lastEvent.counter, remainingCount });
    console.log('f', nodes, {
      node: null,
      remainingCount,
      expectedCounter: lastEvent.counter + remainingCount,
    });
  }
  return {
    node: null,
    remainingCount,
    expectedCounter: lastEvent.counter + remainingCount,
  };
}

function getCounterForRow(state, rowToFind) {
  const { node, remainingCount, parentNode, parentOffset, expectedCounter } =
    _getNodeForRow(state, rowToFind + 1, state.tree);

  if (node) {
    const event = state.events[node.eventIndex];
    return event.counter;
  }
  if (expectedCounter) {
    return expectedCounter;
  }
  // TODO: unclear if any of this is needed. tests pass without but UI seems
  // to get here anyway in some circumstances. If not needed, parentNode and
  // parentOffset might be free to delete above; else add tests!

  debugger;
  // if (parentNode) {
  //   console.log({ parentOffset, remainingCount });
  //   // const parentEvent = state.events[parentNode.eventIndex];
  //   return parentNode.eventIndex + parentOffset;
  // }
  // console.log('OH SHIT');
  // // rowToFind is not a child of any loaded event; look past end of loaded events
  // const lastIndex = Math.max(
  //   ...Object.keys(state.events).map((i) => parseInt(i, 10))
  // );
  // const lastEvent = state.events[String(lastIndex)];
  // return lastEvent.counter + remainingCount;
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
  const { treePath } = state.uuidMap[uuid];
  return {
    ...state,
    tree: _updateNodeByPath(treePath, state.tree, update),
  };
}

function _updateNodeByPath(treePath, nodeArray, update) {
  const index = treePath[0];
  const node = nodeArray[index];
  if (treePath.length === 1) {
    return [
      ...nodeArray.slice(0, index),
      update({ ...node, children: [...nodeArray[index].children] }),
      ...nodeArray.slice(index + 1),
    ];
  }
  return [
    ...nodeArray.slice(0, index),
    {
      ...node,
      children: _updateNodeByPath(treePath.slice(1), node.children, update),
    },
    ...nodeArray.slice(index + 1),
  ];
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

function setEventNumChildren(state, uuid, numChildren) {
  return updateNodeByUuid(state, uuid, (node) => ({
    ...node,
    numChildren,
  }));
}
