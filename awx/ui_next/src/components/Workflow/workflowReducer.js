import { t } from '@lingui/macro';

export function initReducer() {
  return {
    addLinkSourceNode: null,
    addLinkTargetNode: null,
    addNodeSource: null,
    addNodeTarget: null,
    addingLink: false,
    contentError: null,
    isLoading: true,
    linkToDelete: null,
    linkToEdit: null,
    links: [],
    nextNodeId: 0,
    nodePositions: null,
    nodes: [],
    nodeToDelete: null,
    nodeToEdit: null,
    nodeToView: null,
    showDeleteAllNodesModal: false,
    showLegend: false,
    showTools: false,
    showUnsavedChangesModal: false,
    unsavedChanges: false,
  };
}

export default function visualizerReducer(state, action) {
  switch (action.type) {
    case 'CREATE_LINK':
      return createLink(state, action.linkType);
    case 'CREATE_NODE':
      return createNode(state, action.node);
    case 'CANCEL_LINK':
    case 'CANCEL_LINK_MODAL':
      return cancelLink(state);
    case 'CANCEL_NODE_MODAL':
      return {
        ...state,
        addNodeSource: null,
        addNodeTarget: null,
        nodeToEdit: null,
      };
    case 'DELETE_ALL_NODES':
      return deleteAllNodes(state);
    case 'DELETE_LINK':
      return deleteLink(state);
    case 'DELETE_NODE':
      return deleteNode(state);
    case 'GENERATE_NODES_AND_LINKS':
      return generateNodesAndLinks(state, action.nodes, action.i18n);
    case 'RESET':
      return initReducer();
    case 'SELECT_SOURCE_FOR_LINKING':
      return selectSourceForLinking(state, action.node);
    case 'SET_ADD_LINK_TARGET_NODE':
      return { ...state, addLinkTargetNode: action.value };
    case 'SET_CONTENT_ERROR':
      return { ...state, contentError: action.value };
    case 'SET_IS_LOADING':
      return { ...state, isLoading: action.value };
    case 'SET_LINK_TO_DELETE':
      return { ...state, linkToDelete: action.value };
    case 'SET_LINK_TO_EDIT':
      return { ...state, linkToEdit: action.value };
    case 'SET_NODES':
      return { ...state, nodes: action.value };
    case 'SET_NODE_POSITIONS':
      return { ...state, nodePositions: action.value };
    case 'SET_NODE_TO_DELETE':
      return { ...state, nodeToDelete: action.value };
    case 'SET_NODE_TO_EDIT':
      return { ...state, nodeToEdit: action.value };
    case 'SET_NODE_TO_VIEW':
      return { ...state, nodeToView: action.value };
    case 'SET_SHOW_DELETE_ALL_NODES_MODAL':
      return { ...state, showDeleteAllNodesModal: action.value };
    case 'START_ADD_NODE':
      return {
        ...state,
        addNodeSource: action.sourceNodeId,
        addNodeTarget: action.targetNodeId || null,
      };
    case 'START_DELETE_LINK':
      return startDeleteLink(state, action.link);
    case 'TOGGLE_DELETE_ALL_NODES_MODAL':
      return toggleDeleteAllNodesModal(state);
    case 'TOGGLE_LEGEND':
      return toggleLegend(state);
    case 'TOGGLE_TOOLS':
      return toggleTools(state);
    case 'TOGGLE_UNSAVED_CHANGES_MODAL':
      return toggleUnsavedChangesModal(state);
    case 'UPDATE_LINK':
      return updateLink(state, action.linkType);
    case 'UPDATE_NODE':
      return updateNode(state, action.node);
    case 'REFRESH_NODE':
      return refreshNode(state, action.node);
    default:
      throw new Error(`Unrecognized action type: ${action.type}`);
  }
}

function createLink(state, linkType) {
  const { addLinkSourceNode, addLinkTargetNode, links, nodes } = state;
  const newLinks = [...links];
  const newNodes = [...nodes];

  newNodes.forEach(node => {
    node.isInvalidLinkTarget = false;
  });

  newLinks.push({
    source: { id: addLinkSourceNode.id },
    target: { id: addLinkTargetNode.id },
    linkType,
  });

  newLinks.forEach((link, index) => {
    if (link.source.id === 1 && link.target.id === addLinkTargetNode.id) {
      newLinks.splice(index, 1);
    }
  });

  return {
    ...state,
    addLinkSourceNode: null,
    addLinkTargetNode: null,
    addingLink: false,
    linkToEdit: null,
    links: newLinks,
    nodes: newNodes,
    unsavedChanges: true,
  };
}

function createNode(state, node) {
  const { addNodeSource, addNodeTarget, links, nodes, nextNodeId } = state;
  const newNodes = [...nodes];
  const newLinks = [...links];

  newNodes.push({
    id: nextNodeId,
    unifiedJobTemplate: node.nodeResource,
    isInvalidLinkTarget: false,
  });

  // Ensures that root nodes appear to always run
  // after "START"
  if (addNodeSource === 1) {
    node.linkType = 'always';
  }

  newLinks.push({
    source: { id: addNodeSource },
    target: { id: nextNodeId },
    linkType: node.linkType,
  });

  if (addNodeTarget) {
    newLinks.forEach(linkToCompare => {
      if (
        linkToCompare.source.id === addNodeSource &&
        linkToCompare.target.id === addNodeTarget
      ) {
        linkToCompare.source = { id: nextNodeId };
      }
    });
  }

  return {
    ...state,
    addNodeSource: null,
    addNodeTarget: null,
    links: newLinks,
    nextNodeId: nextNodeId + 1,
    nodes: newNodes,
    unsavedChanges: true,
  };
}

function cancelLink(state) {
  const { nodes } = state;
  const newNodes = [...nodes];

  newNodes.forEach(node => {
    node.isInvalidLinkTarget = false;
  });

  return {
    ...state,
    addLinkSourceNode: null,
    addLinkTargetNode: null,
    addingLink: false,
    linkToEdit: null,
    nodes: newNodes,
  };
}

function deleteAllNodes(state) {
  const { nodes } = state;
  return {
    ...state,
    addLinkSourceNode: null,
    addLinkTargetNode: null,
    addingLink: false,
    links: [],
    nodes: nodes.map(node => {
      if (node.id !== 1) {
        node.isDeleted = true;
      }

      return node;
    }),
    showDeleteAllNodesModal: false,
    unsavedChanges: true,
  };
}

function deleteLink(state) {
  const { links, linkToDelete } = state;
  const newLinks = [...links];

  for (let i = newLinks.length; i--; ) {
    const link = newLinks[i];

    if (
      link.source.id === linkToDelete.source.id &&
      link.target.id === linkToDelete.target.id
    ) {
      newLinks.splice(i, 1);
    }
  }

  if (!linkToDelete.isConvergenceLink) {
    // Add a new link from the start node to the orphaned node
    newLinks.push({
      source: {
        id: 1,
      },
      target: {
        id: linkToDelete.target.id,
      },
      linkType: 'always',
    });
  }

  return {
    ...state,
    links: newLinks,
    linkToDelete: null,
    unsavedChanges: true,
  };
}

function addLinksFromParentsToChildren(
  parents,
  children,
  newLinks,
  linkParentMapping
) {
  parents.forEach(parentId => {
    children.forEach(child => {
      if (parentId === 1) {
        // We only want to create a link from the start node to this node if it
        // doesn't have any other parents
        if (linkParentMapping[child.id].length === 1) {
          newLinks.push({
            source: { id: parentId },
            target: { id: child.id },
            linkType: 'always',
          });
        }
      } else if (!linkParentMapping[child.id].includes(parentId)) {
        newLinks.push({
          source: { id: parentId },
          target: { id: child.id },
          linkType: child.linkType,
        });
      }
    });
  });
}

function removeLinksFromDeletedNode(
  nodeId,
  newLinks,
  linkParentMapping,
  children,
  parents
) {
  for (let i = newLinks.length; i--; ) {
    const link = newLinks[i];

    if (!linkParentMapping[link.target.id]) {
      linkParentMapping[link.target.id] = [];
    }

    linkParentMapping[link.target.id].push(link.source.id);

    if (link.source.id === nodeId || link.target.id === nodeId) {
      if (link.source.id === nodeId) {
        children.push({ id: link.target.id, linkType: link.linkType });
      } else if (link.target.id === nodeId) {
        parents.push(link.source.id);
      }
      newLinks.splice(i, 1);
    }
  }
}

function deleteNode(state) {
  const { links, nodes, nodeToDelete } = state;

  const nodeId = nodeToDelete.id;
  const newNodes = [...nodes];
  const newLinks = [...links];

  newNodes.find(node => node.id === nodeToDelete.id).isDeleted = true;

  // Update the links
  const parents = [];
  const children = [];
  const linkParentMapping = {};

  removeLinksFromDeletedNode(
    nodeId,
    newLinks,
    linkParentMapping,
    children,
    parents
  );

  addLinksFromParentsToChildren(parents, children, newLinks, linkParentMapping);

  return {
    ...state,
    links: newLinks,
    nodeToDelete: null,
    nodes: newNodes,
    unsavedChanges: true,
  };
}

function generateNodes(workflowNodes, i18n) {
  const allNodeIds = [];
  const chartNodeIdToIndexMapping = {};
  const nodeIdToChartNodeIdMapping = {};
  let nodeIdCounter = 2;
  const arrayOfNodesForChart = [
    {
      id: 1,
      unifiedJobTemplate: {
        name: i18n._(t`START`),
      },
    },
  ];
  workflowNodes.forEach(node => {
    node.workflowMakerNodeId = nodeIdCounter;

    const nodeObj = {
      id: nodeIdCounter,
      originalNodeObject: node,
    };

    if (node.summary_fields.unified_job_template) {
      nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
    }

    arrayOfNodesForChart.push(nodeObj);
    allNodeIds.push(node.id);
    nodeIdToChartNodeIdMapping[node.id] = node.workflowMakerNodeId;
    chartNodeIdToIndexMapping[nodeIdCounter] = nodeIdCounter - 1;
    nodeIdCounter++;
  });

  return [
    arrayOfNodesForChart,
    allNodeIds,
    nodeIdToChartNodeIdMapping,
    chartNodeIdToIndexMapping,
    nodeIdCounter,
  ];
}

function generateLinks(
  workflowNodes,
  chartNodeIdToIndexMapping,
  nodeIdToChartNodeIdMapping,
  arrayOfNodesForChart
) {
  const arrayOfLinksForChart = [];
  const nonRootNodeIds = [];
  workflowNodes.forEach(node => {
    const sourceIndex = chartNodeIdToIndexMapping[node.workflowMakerNodeId];
    node.success_nodes.forEach(nodeId => {
      const targetIndex =
        chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
      arrayOfLinksForChart.push({
        source: arrayOfNodesForChart[sourceIndex],
        target: arrayOfNodesForChart[targetIndex],
        linkType: 'success',
      });
      nonRootNodeIds.push(nodeId);
    });
    node.failure_nodes.forEach(nodeId => {
      const targetIndex =
        chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
      arrayOfLinksForChart.push({
        source: arrayOfNodesForChart[sourceIndex],
        target: arrayOfNodesForChart[targetIndex],
        linkType: 'failure',
      });
      nonRootNodeIds.push(nodeId);
    });
    node.always_nodes.forEach(nodeId => {
      const targetIndex =
        chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
      arrayOfLinksForChart.push({
        source: arrayOfNodesForChart[sourceIndex],
        target: arrayOfNodesForChart[targetIndex],
        linkType: 'always',
      });
      nonRootNodeIds.push(nodeId);
    });
  });

  return [arrayOfLinksForChart, nonRootNodeIds];
}

// TODO: check to make sure passing i18n into this reducer
// actually works the way we want it to.  If not we may
// have to explore other options
function generateNodesAndLinks(state, workflowNodes, i18n) {
  const [
    arrayOfNodesForChart,
    allNodeIds,
    nodeIdToChartNodeIdMapping,
    chartNodeIdToIndexMapping,
    nodeIdCounter,
  ] = generateNodes(workflowNodes, i18n);
  const [arrayOfLinksForChart, nonRootNodeIds] = generateLinks(
    workflowNodes,
    chartNodeIdToIndexMapping,
    nodeIdToChartNodeIdMapping,
    arrayOfNodesForChart
  );

  const uniqueNonRootNodeIds = Array.from(new Set(nonRootNodeIds));

  const rootNodes = allNodeIds.filter(
    nodeId => !uniqueNonRootNodeIds.includes(nodeId)
  );

  rootNodes.forEach(rootNodeId => {
    const targetIndex =
      chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[rootNodeId]];
    arrayOfLinksForChart.push({
      source: arrayOfNodesForChart[0],
      target: arrayOfNodesForChart[targetIndex],
      linkType: 'always',
    });
  });

  return {
    ...state,
    links: arrayOfLinksForChart,
    nodes: arrayOfNodesForChart,
    nextNodeId: nodeIdCounter,
  };
}

function selectSourceForLinking(state, sourceNode) {
  const { links, nodes } = state;
  const newNodes = [...nodes];
  const parentMap = {};
  const invalidLinkTargetIds = [];
  // Find and mark any ancestors as disabled to prevent cycles
  links.forEach(link => {
    // id=1 is our artificial root node so we don't care about that
    if (link.source.id === 1) {
      return;
    }
    if (link.source.id === sourceNode.id) {
      // Disables direct children from the add link process
      invalidLinkTargetIds.push(link.target.id);
    }
    if (!parentMap[link.target.id]) {
      parentMap[link.target.id] = [];
    }
    parentMap[link.target.id].push(link.source.id);
  });

  const getAncestors = id => {
    if (parentMap[id]) {
      parentMap[id].forEach(parentId => {
        invalidLinkTargetIds.push(parentId);
        getAncestors(parentId);
      });
    }
  };

  getAncestors(sourceNode.id);

  // Filter out the duplicates
  invalidLinkTargetIds
    .filter((element, index, array) => index === array.indexOf(element))
    .forEach(ancestorId => {
      newNodes.forEach(node => {
        if (node.id === ancestorId) {
          node.isInvalidLinkTarget = true;
        }
      });
    });

  return {
    ...state,
    addLinkSourceNode: sourceNode,
    addingLink: true,
    nodes: newNodes,
  };
}

function startDeleteLink(state, link) {
  const { links } = state;
  const parentMap = {};
  links.forEach(existingLink => {
    if (!parentMap[existingLink.target.id]) {
      parentMap[existingLink.target.id] = [];
    }
    parentMap[existingLink.target.id].push(existingLink.source.id);
  });

  link.isConvergenceLink = parentMap[link.target.id].length > 1;

  return {
    ...state,
    linkToDelete: link,
  };
}

function toggleDeleteAllNodesModal(state) {
  const { showDeleteAllNodesModal } = state;
  return {
    ...state,
    showDeleteAllNodesModal: !showDeleteAllNodesModal,
  };
}

function toggleLegend(state) {
  const { showLegend } = state;
  return {
    ...state,
    showLegend: !showLegend,
  };
}

function toggleTools(state) {
  const { showTools } = state;
  return {
    ...state,
    showTools: !showTools,
  };
}

function toggleUnsavedChangesModal(state) {
  const { showUnsavedChangesModal } = state;
  return {
    ...state,
    showUnsavedChangesModal: !showUnsavedChangesModal,
  };
}

function updateLink(state, linkType) {
  const { linkToEdit, links } = state;
  const newLinks = [...links];

  newLinks.forEach(link => {
    if (
      link.source.id === linkToEdit.source.id &&
      link.target.id === linkToEdit.target.id
    ) {
      link.linkType = linkType;
    }
  });

  return {
    ...state,
    linkToEdit: null,
    links: newLinks,
    unsavedChanges: true,
  };
}

function updateNode(state, editedNode) {
  const { nodeToEdit, nodes } = state;
  const newNodes = [...nodes];

  const matchingNode = newNodes.find(node => node.id === nodeToEdit.id);
  matchingNode.unifiedJobTemplate = editedNode.nodeResource;
  matchingNode.isEdited = true;

  return {
    ...state,
    nodeToEdit: null,
    nodes: newNodes,
    unsavedChanges: true,
  };
}

function refreshNode(state, refreshedNode) {
  const { nodeToView, nodes } = state;
  const newNodes = [...nodes];

  const matchingNode = newNodes.find(node => node.id === nodeToView.id);
  matchingNode.unifiedJobTemplate = refreshedNode.nodeResource;

  return {
    ...state,
    nodes: newNodes,
    nodeToView: matchingNode,
  };
}
