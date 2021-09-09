class JobEventsTree {
  constructor({ tree, events, uuidMap, nodesWithoutParents } = {}) {
    // array of root level nodes (event_level: 0)
    this.tree = tree || [];
    this.events = events || {};
    this.uuidMap = uuidMap || {};
    this.nodesWithoutParents = nodesWithoutParents || {};
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

  getNodesWithoutParents() {
    return this.nodesWithoutParents;
  }

  addEvents(newEvents) {
    newEvents.forEach((event) => {
      // todo normalize?
      const eventIndex = event.counter;
      if (this.events[eventIndex]) {
        this.events[eventIndex] = event;
        return;
      }
      this.events[eventIndex] = event;
      if (event.event_level === 0) {
        // TODO add to array in correct position
        const length = this.tree.push({
          eventIndex,
          isCollapsed: false,
          children: [],
        });
        this.uuidMap[event.uuid] = {
          index: eventIndex,
          treePath: [length - 1],
        };
        return;
      }

      // todo: what if parent missing?
      const parent = this.getNodeByUuid(event.parent_uuid);
      const length = parent.children.push({
        eventIndex,
        isCollapsed: false,
        children: [],
      });
      const { treePath: parentTreePath } = this.uuidMap[event.parent_uuid];
      this.uuidMap[event.uuid] = {
        index: eventIndex,
        treePath: [...parentTreePath, length - 1],
      };
    });
    // todo: clean out un-needed(?) events if too many in memory?
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
