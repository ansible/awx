class JobEventsTree {
  constructor({ tree, events, uuidMap } = {}) {
    // array of root level nodes (event_level: 0)
    this.tree = tree || [];
    this.events = events || {};
    this.uuidMap = uuidMap || {};
  }

  getAllEvents() {
    return this.events;
  }

  getEventTree() {
    return this.tree;
  }

  addEvents(newEvents) {
    newEvents.forEach((event) => {
      // todo normalize?
      const eventIndex = event.counter;
      this.events[eventIndex] = event;
      if (event.event_level === 0) {
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

  getNodeForRow(rowToFind) {
    const [node] = this._getNodeForRow(rowToFind + 1, this.tree);
    return node;
  }

  _getNodeForRow(rowToFind, nodes) {
    for (let i = 0; i < nodes.length; i++) {
      const node = nodes[i];
      if (this.events[node.eventIndex].counter === rowToFind) {
        return [node, rowToFind];
      }
      if (node.isCollapsed) {
        rowToFind += this.getTotalNumChildren(node);
        continue;
      }
      const { eventIndex: nextIndex } = nodes[i + 1] || {};
      if (!nextIndex || nextIndex > rowToFind) {
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

  getTotalNumChildren(node) {
    return node.children.reduce(
      (sumChildren, currentNode) =>
        sumChildren + this.getTotalNumChildren(currentNode),
      node.children.length
    );
  }

  getNodeByUuid(uuid) {
    const { treePath = [] } = this.uuidMap[uuid] || {};
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
