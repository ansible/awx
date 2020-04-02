import workflowReducer, { initReducer } from './workflowReducer';

const defaultState = {
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

describe('Workflow reducer', () => {
  describe('CREATE_LINK', () => {
    it('should clear the isInvalidLinkTarget flag from all nodes and add new link', () => {
      const state = {
        ...defaultState,
        addLinkSourceNode: { id: 2 },
        addLinkTargetNode: { id: 4 },
        addingLink: true,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: true,
          },
          {
            id: 2,
            isInvalidLinkTarget: true,
          },
          {
            id: 3,
            isInvalidLinkTarget: true,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'CREATE_LINK',
        linkType: 'always',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
        unsavedChanges: true,
      });
    });
  });
  describe('CREATE_NODE', () => {
    it('should add new node and link from the end of the source node when no target node present', () => {
      const state = {
        ...defaultState,
        addNodeSource: 1,
        isLoading: false,
        nextNodeId: 2,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'CREATE_NODE',
        node: {
          linkType: 'always',
          nodeResource: {
            id: 7000,
            name: 'Foo JT',
          },
        },
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 3,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
            unifiedJobTemplate: {
              id: 7000,
              name: 'Foo JT',
            },
          },
        ],
        unsavedChanges: true,
      });
    });
    it('should add new node and link between the source and target nodes when target node present', () => {
      const state = {
        ...defaultState,
        addNodeSource: 1,
        addNodeTarget: 2,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 3,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'CREATE_NODE',
        node: {
          linkType: 'always',
          nodeResource: {
            id: 7000,
            name: 'Foo JT',
          },
        },
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 3,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 1,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 4,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
            unifiedJobTemplate: {
              id: 7000,
              name: 'Foo JT',
            },
          },
        ],
        unsavedChanges: true,
      });
    });
  });
  describe('CANCEL_LINK/CANCEL_LINK_MODAL', () => {
    it('should wipe flags that track the process of adding or editing a link', () => {
      const state = {
        ...defaultState,
        addLinkSourceNode: { id: 2 },
        addLinkTargetNode: { id: 4 },
        addingLink: true,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: true,
          },
          {
            id: 2,
            isInvalidLinkTarget: true,
          },
          {
            id: 3,
            isInvalidLinkTarget: true,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
        unsavedChanges: false,
      };
      const result = workflowReducer(state, {
        type: 'CANCEL_LINK',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
      });
    });
  });
  describe('CANCEL_NODE_MODAL', () => {
    it('should wipe the flags that track the process of adding a node', () => {
      const state = {
        ...defaultState,
        addNodeSource: { id: 1 },
        isLoading: false,
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'CANCEL_NODE_MODAL',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
        ],
      });
    });
    it('should wipe the flags that track the process of editing a node', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
        ],
        nodeToEdit: {
          id: 2,
        },
      };
      const result = workflowReducer(state, {
        type: 'CANCEL_NODE_MODAL',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
        ],
      });
    });
  });
  describe('DELETE_ALL_NODES', () => {
    it('should mark all the non-start nodes as deleted and clear out the links', () => {
      const state = {
        ...defaultState,
        addLinkSourceNode: { id: 2 },
        addLinkTargetNode: { id: 4 },
        addingLink: true,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'DELETE_ALL_NODES',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
            isDeleted: true,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
            isDeleted: true,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
            isDeleted: true,
          },
        ],
        unsavedChanges: true,
      });
    });
  });
  describe('DELETE_LINK', () => {
    it('should remove the link and connect the remaining node to start if orphaned', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        linkToDelete: {
          source: {
            id: 3,
          },
          target: {
            id: 4,
          },
          linkType: 'always',
        },
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'DELETE_LINK',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 1,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
        unsavedChanges: true,
      });
    });
  });
  describe('DELETE_NODE', () => {
    it('should remove the mark the node as deleted and re-link any orphaned nodes', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
        nodeToDelete: {
          id: 3,
        },
      };
      const result = workflowReducer(state, {
        type: 'DELETE_NODE',
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
            isDeleted: true,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
        unsavedChanges: true,
      });
    });
  });
  describe('GENERATE_NODES_AND_LINKS', () => {
    it('should generate the correct node and link arrays', () => {
      const result = workflowReducer(defaultState, {
        type: 'GENERATE_NODES_AND_LINKS',
        nodes: [
          {
            id: 1,
            success_nodes: [3],
            failure_nodes: [],
            always_nodes: [2],
            summary_fields: {
              unified_job_template: {
                id: 1,
                name: 'JT 1',
              },
            },
          },
          {
            id: 2,
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
            summary_fields: {
              unified_job_template: {
                id: 2,
                name: 'JT 2',
              },
            },
          },
          {
            id: 3,
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [],
            summary_fields: {
              unified_job_template: {
                id: 3,
                name: 'JT 3',
              },
            },
          },
          {
            id: 4,
            success_nodes: [],
            failure_nodes: [],
            always_nodes: [2],
            summary_fields: {
              unified_job_template: {
                id: 4,
                name: 'JT 4',
              },
            },
          },
        ],
        i18n: {
          _: () => {},
        },
      });
      expect(result).toEqual({
        ...defaultState,
        links: [
          {
            linkType: 'success',
            source: {
              id: 2,
              originalNodeObject: {
                always_nodes: [2],
                failure_nodes: [],
                id: 1,
                success_nodes: [3],
                summary_fields: {
                  unified_job_template: {
                    id: 1,
                    name: 'JT 1',
                  },
                },
                workflowMakerNodeId: 2,
              },
              unifiedJobTemplate: {
                id: 1,
                name: 'JT 1',
              },
            },
            target: {
              id: 4,
              originalNodeObject: {
                always_nodes: [],
                failure_nodes: [],
                id: 3,
                success_nodes: [],
                summary_fields: {
                  unified_job_template: {
                    id: 3,
                    name: 'JT 3',
                  },
                },
                workflowMakerNodeId: 4,
              },
              unifiedJobTemplate: {
                id: 3,
                name: 'JT 3',
              },
            },
          },
          {
            linkType: 'always',
            source: {
              id: 2,
              originalNodeObject: {
                always_nodes: [2],
                failure_nodes: [],
                id: 1,
                success_nodes: [3],
                summary_fields: {
                  unified_job_template: {
                    id: 1,
                    name: 'JT 1',
                  },
                },
                workflowMakerNodeId: 2,
              },
              unifiedJobTemplate: {
                id: 1,
                name: 'JT 1',
              },
            },
            target: {
              id: 3,
              originalNodeObject: {
                always_nodes: [],
                failure_nodes: [],
                id: 2,
                success_nodes: [],
                summary_fields: {
                  unified_job_template: {
                    id: 2,
                    name: 'JT 2',
                  },
                },
                workflowMakerNodeId: 3,
              },
              unifiedJobTemplate: {
                id: 2,
                name: 'JT 2',
              },
            },
          },
          {
            linkType: 'always',
            source: {
              id: 5,
              originalNodeObject: {
                always_nodes: [2],
                failure_nodes: [],
                id: 4,
                success_nodes: [],
                summary_fields: {
                  unified_job_template: {
                    id: 4,
                    name: 'JT 4',
                  },
                },
                workflowMakerNodeId: 5,
              },
              unifiedJobTemplate: {
                id: 4,
                name: 'JT 4',
              },
            },
            target: {
              id: 3,
              originalNodeObject: {
                always_nodes: [],
                failure_nodes: [],
                id: 2,
                success_nodes: [],
                summary_fields: {
                  unified_job_template: {
                    id: 2,
                    name: 'JT 2',
                  },
                },
                workflowMakerNodeId: 3,
              },
              unifiedJobTemplate: {
                id: 2,
                name: 'JT 2',
              },
            },
          },
          {
            linkType: 'always',
            source: {
              id: 1,
              unifiedJobTemplate: {
                name: undefined,
              },
            },
            target: {
              id: 2,
              originalNodeObject: {
                always_nodes: [2],
                failure_nodes: [],
                id: 1,
                success_nodes: [3],
                summary_fields: {
                  unified_job_template: {
                    id: 1,
                    name: 'JT 1',
                  },
                },
                workflowMakerNodeId: 2,
              },
              unifiedJobTemplate: {
                id: 1,
                name: 'JT 1',
              },
            },
          },
          {
            linkType: 'always',
            source: {
              id: 1,
              unifiedJobTemplate: {
                name: undefined,
              },
            },
            target: {
              id: 5,
              originalNodeObject: {
                always_nodes: [2],
                failure_nodes: [],
                id: 4,
                success_nodes: [],
                summary_fields: {
                  unified_job_template: {
                    id: 4,
                    name: 'JT 4',
                  },
                },
                workflowMakerNodeId: 5,
              },
              unifiedJobTemplate: {
                id: 4,
                name: 'JT 4',
              },
            },
          },
        ],
        nextNodeId: 6,
        nodes: [
          {
            id: 1,
            unifiedJobTemplate: {
              name: undefined,
            },
          },
          {
            id: 2,
            originalNodeObject: {
              always_nodes: [2],
              failure_nodes: [],
              id: 1,
              success_nodes: [3],
              summary_fields: {
                unified_job_template: {
                  id: 1,
                  name: 'JT 1',
                },
              },
              workflowMakerNodeId: 2,
            },
            unifiedJobTemplate: {
              id: 1,
              name: 'JT 1',
            },
          },
          {
            id: 3,
            originalNodeObject: {
              always_nodes: [],
              failure_nodes: [],
              id: 2,
              success_nodes: [],
              summary_fields: {
                unified_job_template: {
                  id: 2,
                  name: 'JT 2',
                },
              },
              workflowMakerNodeId: 3,
            },
            unifiedJobTemplate: {
              id: 2,
              name: 'JT 2',
            },
          },
          {
            id: 4,
            originalNodeObject: {
              always_nodes: [],
              failure_nodes: [],
              id: 3,
              success_nodes: [],
              summary_fields: {
                unified_job_template: {
                  id: 3,
                  name: 'JT 3',
                },
              },
              workflowMakerNodeId: 4,
            },
            unifiedJobTemplate: {
              id: 3,
              name: 'JT 3',
            },
          },
          {
            id: 5,
            originalNodeObject: {
              always_nodes: [2],
              failure_nodes: [],
              id: 4,
              success_nodes: [],
              summary_fields: {
                unified_job_template: {
                  id: 4,
                  name: 'JT 4',
                },
              },
              workflowMakerNodeId: 5,
            },
            unifiedJobTemplate: {
              id: 4,
              name: 'JT 4',
            },
          },
        ],
      });
    });
  });
  describe('RESET', () => {
    it('should reset the state back to default values', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
          },
        ],
        nextNodeId: 3,
        nodes: [
          {
            id: 1,
          },
          {
            id: 2,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'RESET',
      });
      expect(result).toEqual(defaultState);
    });
  });
  describe('SELECT_SOURCE_FOR_LINKING', () => {
    it('should set source node and mark invalid target nodes', () => {
      const sourceNode = {
        id: 3,
        isInvalidLinkTarget: false,
      };
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 1,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 5,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 6,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          sourceNode,
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
          {
            id: 5,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'SELECT_SOURCE_FOR_LINKING',
        node: sourceNode,
      });
      expect(result).toEqual({
        ...defaultState,
        addLinkSourceNode: sourceNode,
        addingLink: true,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 1,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 5,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 6,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          sourceNode,
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
          {
            id: 5,
            isInvalidLinkTarget: true,
          },
        ],
      });
    });
  });
  describe('SET_ADD_LINK_TARGET_NODE', () => {
    it('should set the state variable', () => {
      const result = workflowReducer(defaultState, {
        type: 'SET_ADD_LINK_TARGET_NODE',
        value: {
          id: 2,
        },
      });
      expect(result).toEqual({
        ...defaultState,
        addLinkTargetNode: {
          id: 2,
        },
      });
    });
  });
  describe('SET_CONTENT_ERROR', () => {
    it('should set the state variable', () => {
      const result = workflowReducer(defaultState, {
        type: 'SET_CONTENT_ERROR',
        value: new Error('Test Error'),
      });
      expect(result).toEqual({
        ...defaultState,
        contentError: new Error('Test Error'),
      });
    });
  });
  describe('SET_IS_LOADING', () => {
    it('should set the state variable', () => {
      const result = workflowReducer(defaultState, {
        type: 'SET_IS_LOADING',
        value: false,
      });
      expect(result).toEqual({
        ...defaultState,
        isLoading: false,
      });
    });
  });
  describe('SET_LINK_TO_DELETE', () => {
    it('should set the state variable', () => {
      const linkToDelete = {
        source: {
          id: 2,
        },
        target: {
          id: 3,
        },
        linkType: 'always',
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_LINK_TO_DELETE',
        value: linkToDelete,
      });
      expect(result).toEqual({
        ...defaultState,
        linkToDelete,
      });
    });
  });
  describe('SET_LINK_TO_EDIT', () => {
    it('should set the state variable', () => {
      const linkToEdit = {
        source: {
          id: 2,
        },
        target: {
          id: 3,
        },
        linkType: 'always',
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_LINK_TO_EDIT',
        value: linkToEdit,
      });
      expect(result).toEqual({
        ...defaultState,
        linkToEdit,
      });
    });
  });
  describe('SET_NODE_POSITIONS', () => {
    it('should set the state variable', () => {
      const nodePositions = {
        label: '',
        width: 72,
        height: 40,
        x: 36,
        y: 20,
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_NODE_POSITIONS',
        value: nodePositions,
      });
      expect(result).toEqual({
        ...defaultState,
        nodePositions,
      });
    });
  });
  describe('SET_NODE_TO_DELETE', () => {
    it('should set the state variable', () => {
      const nodeToDelete = {
        id: 2,
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_NODE_TO_DELETE',
        value: nodeToDelete,
      });
      expect(result).toEqual({
        ...defaultState,
        nodeToDelete,
      });
    });
  });
  describe('SET_NODE_TO_EDIT', () => {
    it('should set the state variable', () => {
      const nodeToEdit = {
        id: 2,
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_NODE_TO_EDIT',
        value: nodeToEdit,
      });
      expect(result).toEqual({
        ...defaultState,
        nodeToEdit,
      });
    });
  });
  describe('SET_NODE_TO_VIEW', () => {
    it('should set the state variable', () => {
      const nodeToView = {
        id: 2,
      };
      const result = workflowReducer(defaultState, {
        type: 'SET_NODE_TO_VIEW',
        value: nodeToView,
      });
      expect(result).toEqual({
        ...defaultState,
        nodeToView,
      });
    });
  });
  describe('START_ADD_NODE', () => {
    it('should set the source/target node ids to state', () => {
      const result = workflowReducer(defaultState, {
        type: 'START_ADD_NODE',
        sourceNodeId: 44,
        targetNodeId: 9000,
      });
      expect(result).toEqual({
        ...defaultState,
        addNodeSource: 44,
        addNodeTarget: 9000,
      });
    });
  });
  describe('START_DELETE_LINK', () => {
    it('should update the link to indicate whether it is a convergence link and update the state variable', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 1,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 3,
            },
            target: {
              id: 4,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 5,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
          {
            id: 4,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const result = workflowReducer(state, {
        type: 'START_DELETE_LINK',
        link: {
          source: {
            id: 3,
          },
          target: {
            id: 4,
          },
          linkType: 'always',
        },
      });
      expect(result).toEqual({
        ...state,
        linkToDelete: {
          source: {
            id: 3,
          },
          target: {
            id: 4,
          },
          isConvergenceLink: true,
          linkType: 'always',
        },
      });
    });
  });
  describe('TOGGLE_DELETE_ALL_NODES_MODAL', () => {
    it('should toggle the show delete all nodes modal flag', () => {
      const firstToggleState = workflowReducer(defaultState, {
        type: 'TOGGLE_DELETE_ALL_NODES_MODAL',
      });
      expect(firstToggleState).toEqual({
        ...defaultState,
        showDeleteAllNodesModal: true,
      });
      const secondToggleState = workflowReducer(firstToggleState, {
        type: 'TOGGLE_DELETE_ALL_NODES_MODAL',
      });
      expect(secondToggleState).toEqual(defaultState);
    });
  });
  describe('TOGGLE_LEGEND', () => {
    it('should toggle the show legend flag', () => {
      const firstToggleState = workflowReducer(defaultState, {
        type: 'TOGGLE_LEGEND',
      });
      expect(firstToggleState).toEqual({
        ...defaultState,
        showLegend: true,
      });
      const secondToggleState = workflowReducer(firstToggleState, {
        type: 'TOGGLE_LEGEND',
      });
      expect(secondToggleState).toEqual(defaultState);
    });
  });
  describe('TOGGLE_TOOLS', () => {
    it('should toggle the show legend flag', () => {
      const firstToggleState = workflowReducer(defaultState, {
        type: 'TOGGLE_TOOLS',
      });
      expect(firstToggleState).toEqual({
        ...defaultState,
        showTools: true,
      });
      const secondToggleState = workflowReducer(firstToggleState, {
        type: 'TOGGLE_TOOLS',
      });
      expect(secondToggleState).toEqual(defaultState);
    });
  });
  describe('TOGGLE_UNSAVED_CHANGES_MODAL', () => {
    it('should toggle the unsaved changes modal flag', () => {
      const firstToggleState = workflowReducer(defaultState, {
        type: 'TOGGLE_UNSAVED_CHANGES_MODAL',
      });
      expect(firstToggleState).toEqual({
        ...defaultState,
        showUnsavedChangesModal: true,
      });
      const secondToggleState = workflowReducer(firstToggleState, {
        type: 'TOGGLE_UNSAVED_CHANGES_MODAL',
      });
      expect(secondToggleState).toEqual(defaultState);
    });
  });
  describe('UPDATE_LINK', () => {
    it('should update the link type', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'always',
          },
        ],
        linkToEdit: {
          source: {
            id: 2,
          },
          target: {
            id: 3,
          },
          linkType: 'always',
        },
        nextNodeId: 4,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isInvalidLinkTarget: false,
          },
          {
            id: 3,
            isInvalidLinkTarget: false,
          },
        ],
      };
      const firstToggleState = workflowReducer(state, {
        type: 'UPDATE_LINK',
        linkType: 'success',
      });
      expect(firstToggleState).toEqual({
        ...state,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
          {
            source: {
              id: 2,
            },
            target: {
              id: 3,
            },
            linkType: 'success',
          },
        ],
        linkToEdit: null,
        unsavedChanges: true,
      });
    });
  });
  describe('UPDATE_NODE', () => {
    it('should update the node', () => {
      const state = {
        ...defaultState,
        isLoading: false,
        links: [
          {
            source: {
              id: 1,
            },
            target: {
              id: 2,
            },
            linkType: 'always',
          },
        ],
        nextNodeId: 3,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isEdited: false,
            isInvalidLinkTarget: false,
            unifiedJobTemplate: {
              id: 703,
              name: 'Test JT',
              type: 'job_template',
            },
          },
        ],
        nodeToEdit: {
          id: 2,
          isEdited: false,
          isInvalidLinkTarget: false,
          unifiedJobTemplate: {
            id: 703,
            name: 'Test JT',
            type: 'job_template',
          },
        },
      };
      const firstToggleState = workflowReducer(state, {
        type: 'UPDATE_NODE',
        node: {
          nodeResource: {
            id: 704,
            name: 'Other JT',
            type: 'job_template',
          },
        },
      });
      expect(firstToggleState).toEqual({
        ...state,
        nodes: [
          {
            id: 1,
            isInvalidLinkTarget: false,
          },
          {
            id: 2,
            isEdited: true,
            isInvalidLinkTarget: false,
            unifiedJobTemplate: {
              id: 704,
              name: 'Other JT',
              type: 'job_template',
            },
          },
        ],
        nodeToEdit: null,
        unsavedChanges: true,
      });
    });
  });
  describe('initReducer', () => {
    it('should init', () => {
      const state = initReducer();
      expect(state).toEqual(defaultState);
    });
  });
});
