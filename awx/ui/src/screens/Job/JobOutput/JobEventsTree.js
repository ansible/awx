class JobEventsTree {
  constructor(
    { tree, events, uuidMap, eventsWithoutParents } = {},
    fetchEventByUuid
  ) {
    // array of root level nodes (event_level: 0)
    this.tree = tree || [];
    // all events indexed by counter value
    this.events = events || {};
    // lookup info (counter value & location in tree) indexed by uuid
    this.uuidMap = uuidMap || {};
    // events with parent events that aren't yet loaded.
    // arrays indexed by parent uuid
    this.eventsWithoutParents = eventsWithoutParents || {};
    this.fetchEventByUuid = fetchEventByUuid || (() => {});
  }

  getAllEvents() {
    return this.events;
  }

  getEvent(index) {
    return this.events[index];
  }

  getEventTree() {
    return this.tree;
  }

  getEventsWithoutParents() {
    return this.eventsWithoutParents;
  }

  addEvents(newEvents) {
    const parentsToFetch = new Set();
    newEvents.forEach((event) => {
      // todo normalize?
      const eventIndex = event.counter;
      if (this.events[eventIndex]) {
        this.events[eventIndex] = event;
        this._gatherEventsForNewParent(event.uuid);
        return;
      }
      if (event.event_level === 0) {
        this._addRootLevelEvent(event);
        this.events[eventIndex] = event;
        return;
      }

      const isParentFound = this._addNestedLevelEvent(event);
      if (isParentFound) {
        this.events[eventIndex] = event;
      } else {
        parentsToFetch.add(event.parent_uuid);
        this._addEventWithoutParent(event);
      }
    });

    parentsToFetch.forEach((uuid) => this.fetchEventByUuid(uuid));
  }

  _addRootLevelEvent(event) {
    const eventIndex = event.counter;
    const newNode = {
      eventIndex,
      isCollapsed: false,
      children: [],
    };
    const index = this.tree.findIndex((node) => node.eventIndex > eventIndex);
    let length;
    if (index === -1) {
      length = this.tree.push(newNode);
    } else {
      this.tree.splice(index, 0, newNode);
      length = this.tree.length;
    }
    this.uuidMap[event.uuid] = {
      index: eventIndex,
      treePath: [length - 1],
    };
    this._gatherEventsForNewParent(event.uuid);
  }

  _addNestedLevelEvent(event) {
    const eventIndex = event.counter;
    const parent = this.getNodeByUuid(event.parent_uuid);
    if (!parent) {
      return false;
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
    if (index === -1) {
      length = parent.children.push(newNode);
    } else {
      parent.children.splice(index, 0, newNode);
      length = parent.children.length;
    }
    const { treePath: parentTreePath } = this.uuidMap[event.parent_uuid];
    this.uuidMap[event.uuid] = {
      index: eventIndex,
      treePath: [...parentTreePath, length - 1],
    };
    this._gatherEventsForNewParent(event.uuid);

    return true;
  }

  _addEventWithoutParent(event) {
    const parentUuid = event.parent_uuid;
    if (!this.eventsWithoutParents[parentUuid]) {
      this.eventsWithoutParents = {
        ...this.eventsWithoutParents,
        [parentUuid]: [event],
      };
      return;
    }

    this.eventsWithoutParents = {
      ...this.eventsWithoutParents,
      [parentUuid]: this.eventsWithoutParents[parentUuid].concat(event),
    };
  }

  _gatherEventsForNewParent(parentUuid) {
    if (!this.eventsWithoutParents[parentUuid]) {
      return;
    }

    const { [parentUuid]: events, ...remaining } = this.eventsWithoutParents;
    this.eventsWithoutParents = remaining;
    this.addEvents(events);
  }

  getEventForRow(rowIndex) {
    const node = this.getNodeForRow(rowIndex);
    if (!node) {
      return null;
    }
    return {
      node,
      event: this.events[node.eventIndex],
    };
  }

  getNodeForRow(rowToFind) {
    const [node] = this._getNodeForRow(rowToFind + 1, this.tree);
    return node;
  }

  _getNodeForRow(rowToFind, nodes) {
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      const nextNode = nodes[i + 1] || {};
      if (this.events[node.eventIndex].counter === rowToFind) {
        return [node, rowToFind];
      }
      if (node.isCollapsed) {
        // const numHiddenEvents = nextNode.eventIndex
        //   ? nextNode.eventIndex - node.eventIndex - 1
        //   : this.getTotalChildren(node);
        rowToFind += this.getTotalNumChildren(node, nextNode);
        // rowToFind += numHiddenEvents;
        continue;
      }
      if (!nextNode.eventIndex || nextNode.eventIndex > rowToFind) {
        const [found, newRowToFind] = this._getNodeForRow(
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

  getTotalNumChildren(node, siblingNode = null) {
    // GOTCHA: requires no un-loaded siblings between node & siblingNode
    if (siblingNode?.eventIndex) {
      return siblingNode.eventIndex - node.eventIndex - 1;
    }
    let sum = node.children.length;
    node.children.forEach((child, i) => {
      sum += this.getTotalNumChildren(child, node.children[i + 1]);
    });
    return sum;
  }

  getNodeByUuid(uuid) {
    if (!this.uuidMap[uuid]) {
      return null;
    }
    const { treePath } = this.uuidMap[uuid];
    let arr = this.tree;
    let lastNode;
    for (let i = 0; i < treePath.length; i++) {
      const index = treePath[i];
      lastNode = arr[index];
      arr = arr[index].children;
    }
    return lastNode;
  }

  toggleNodeIsCollapsed(eventUuid) {
    const node = this.getNodeByUuid(eventUuid);
    if (!node) {
      throw new Error(`Node not found Event UUID ${eventUuid}`);
    }
    node.isCollapsed = !node.isCollapsed;
    // TODO: update remoteRowCount
  }

  // cssMap
  // remote row count?
}

export default JobEventsTree;
