import React, { useEffect, useReducer } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';
import { shape } from 'prop-types';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { layoutGraph } from '../../../components/Workflow/WorkflowUtils';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import workflowReducer from '../../../components/Workflow/workflowReducer';
import { DeleteAllNodesModal, UnsavedChangesModal } from './Modals';
import {
  LinkAddModal,
  LinkDeleteModal,
  LinkEditModal,
} from './Modals/LinkModals';
import {
  NodeAddModal,
  NodeEditModal,
  NodeDeleteModal,
  NodeViewModal,
} from './Modals/NodeModals';
import VisualizerGraph from './VisualizerGraph';
import VisualizerStartScreen from './VisualizerStartScreen';
import VisualizerToolbar from './VisualizerToolbar';
import {
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from '../../../api';

const CenteredContent = styled.div`
  align-items: center;
  display: flex;
  flex-flow: column;
  height: 100%;
  justify-content: center;
`;

const Wrapper = styled.div`
  display: flex;
  flex-flow: column;
  height: 100%;
`;

const fetchWorkflowNodes = async (
  templateId,
  pageNo = 1,
  workflowNodes = []
) => {
  const { data } = await WorkflowJobTemplatesAPI.readNodes(templateId, {
    page_size: 200,
    page: pageNo,
  });
  if (data.next) {
    return fetchWorkflowNodes(
      templateId,
      pageNo + 1,
      workflowNodes.concat(data.results)
    );
  }
  return workflowNodes.concat(data.results);
};

function Visualizer({ template, i18n }) {
  const history = useHistory();
  const [state, dispatch] = useReducer(workflowReducer, {
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
    nodeToDelete: null,
    nodeToEdit: null,
    nodeToView: null,
    nodes: [],
    showDeleteAllNodesModal: false,
    showLegend: false,
    showTools: false,
    showUnsavedChangesModal: false,
    unsavedChanges: false,
  });

  const {
    addLinkSourceNode,
    addLinkTargetNode,
    addNodeSource,
    contentError,
    isLoading,
    linkToDelete,
    linkToEdit,
    links,
    nodeToDelete,
    nodeToEdit,
    nodeToView,
    nodes,
    showDeleteAllNodesModal,
    showUnsavedChangesModal,
    unsavedChanges,
  } = state;

  const handleVisualizerClose = () => {
    if (unsavedChanges) {
      dispatch({ type: 'TOGGLE_UNSAVED_CHANGES_MODAL' });
    } else {
      history.push(`/templates/workflow_job_template/${template.id}/details`);
    }
  };

  const associateNodes = (newLinks, originalLinkMap) => {
    const associateNodeRequests = [];
    newLinks.forEach(link => {
      switch (link.linkType) {
        case 'success':
          associateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.associateSuccessNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        case 'failure':
          associateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.associateFailureNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        case 'always':
          associateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.associateAlwaysNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        default:
      }
    });

    return associateNodeRequests;
  };

  const disassociateNodes = (originalLinkMap, deletedNodeIds, linkMap) => {
    const disassociateNodeRequests = [];
    Object.keys(originalLinkMap).forEach(key => {
      const node = originalLinkMap[key];
      node.success_nodes.forEach(successNodeId => {
        if (
          !deletedNodeIds.includes(successNodeId) &&
          (!linkMap[node.id] ||
            !linkMap[node.id][successNodeId] ||
            linkMap[node.id][successNodeId] !== 'success')
        ) {
          disassociateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.disassociateSuccessNode(
              node.id,
              successNodeId
            )
          );
        }
      });
      node.failure_nodes.forEach(failureNodeId => {
        if (
          !deletedNodeIds.includes(failureNodeId) &&
          (!linkMap[node.id] ||
            !linkMap[node.id][failureNodeId] ||
            linkMap[node.id][failureNodeId] !== 'failure')
        ) {
          disassociateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.disassociateFailuresNode(
              node.id,
              failureNodeId
            )
          );
        }
      });
      node.always_nodes.forEach(alwaysNodeId => {
        if (
          !deletedNodeIds.includes(alwaysNodeId) &&
          (!linkMap[node.id] ||
            !linkMap[node.id][alwaysNodeId] ||
            linkMap[node.id][alwaysNodeId] !== 'always')
        ) {
          disassociateNodeRequests.push(
            WorkflowJobTemplateNodesAPI.disassociateAlwaysNode(
              node.id,
              alwaysNodeId
            )
          );
        }
      });
    });

    return disassociateNodeRequests;
  };

  const generateLinkMapAndNewLinks = originalLinkMap => {
    const linkMap = {};
    const newLinks = [];

    links.forEach(link => {
      if (link.source.id !== 1) {
        const realLinkSourceId = originalLinkMap[link.source.id].id;
        const realLinkTargetId = originalLinkMap[link.target.id].id;
        if (!linkMap[realLinkSourceId]) {
          linkMap[realLinkSourceId] = {};
        }
        linkMap[realLinkSourceId][realLinkTargetId] = link.linkType;
        switch (link.linkType) {
          case 'success':
            if (
              !originalLinkMap[link.source.id].success_nodes.includes(
                originalLinkMap[link.target.id].id
              )
            ) {
              newLinks.push(link);
            }
            break;
          case 'failure':
            if (
              !originalLinkMap[link.source.id].failure_nodes.includes(
                originalLinkMap[link.target.id].id
              )
            ) {
              newLinks.push(link);
            }
            break;
          case 'always':
            if (
              !originalLinkMap[link.source.id].always_nodes.includes(
                originalLinkMap[link.target.id].id
              )
            ) {
              newLinks.push(link);
            }
            break;
          default:
        }
      }
    });

    return [linkMap, newLinks];
  };

  const handleVisualizerSave = async () => {
    const nodeRequests = [];
    const approvalTemplateRequests = [];
    const originalLinkMap = {};
    const deletedNodeIds = [];
    nodes.forEach(node => {
      // node with id=1 is the artificial start node
      if (node.id === 1) {
        return;
      }
      if (node.originalNodeObject && !node.isDeleted) {
        const {
          id,
          success_nodes,
          failure_nodes,
          always_nodes,
        } = node.originalNodeObject;
        originalLinkMap[node.id] = {
          id,
          success_nodes,
          failure_nodes,
          always_nodes,
        };
      }
      if (node.isDeleted && node.originalNodeObject) {
        deletedNodeIds.push(node.originalNodeObject.id);
        nodeRequests.push(
          WorkflowJobTemplateNodesAPI.destroy(node.originalNodeObject.id)
        );
      } else if (!node.isDeleted && !node.originalNodeObject) {
        if (node.unifiedJobTemplate.type === 'workflow_approval_template') {
          nodeRequests.push(
            WorkflowJobTemplatesAPI.createNode(template.id, {}).then(
              ({ data }) => {
                node.originalNodeObject = data;
                originalLinkMap[node.id] = {
                  id: data.id,
                  success_nodes: [],
                  failure_nodes: [],
                  always_nodes: [],
                };
                approvalTemplateRequests.push(
                  WorkflowJobTemplateNodesAPI.createApprovalTemplate(data.id, {
                    name: node.unifiedJobTemplate.name,
                    description: node.unifiedJobTemplate.description,
                    timeout: node.unifiedJobTemplate.timeout,
                  })
                );
              }
            )
          );
        } else {
          nodeRequests.push(
            WorkflowJobTemplatesAPI.createNode(template.id, {
              unified_job_template: node.unifiedJobTemplate.id,
            }).then(({ data }) => {
              node.originalNodeObject = data;
              originalLinkMap[node.id] = {
                id: data.id,
                success_nodes: [],
                failure_nodes: [],
                always_nodes: [],
              };
            })
          );
        }
      } else if (node.isEdited) {
        if (
          node.unifiedJobTemplate &&
          (node.unifiedJobTemplate.unified_job_type === 'workflow_approval' ||
            node.unifiedJobTemplate.type === 'workflow_approval_template')
        ) {
          if (
            node.originalNodeObject.summary_fields.unified_job_template
              .unified_job_type === 'workflow_approval'
          ) {
            approvalTemplateRequests.push(
              WorkflowApprovalTemplatesAPI.update(
                node.originalNodeObject.summary_fields.unified_job_template.id,
                {
                  name: node.unifiedJobTemplate.name,
                  description: node.unifiedJobTemplate.description,
                  timeout: node.unifiedJobTemplate.timeout,
                }
              )
            );
          } else {
            approvalTemplateRequests.push(
              WorkflowJobTemplateNodesAPI.createApprovalTemplate(
                node.originalNodeObject.id,
                {
                  name: node.unifiedJobTemplate.name,
                  description: node.unifiedJobTemplate.description,
                  timeout: node.unifiedJobTemplate.timeout,
                }
              )
            );
          }
        } else {
          nodeRequests.push(
            WorkflowJobTemplateNodesAPI.update(node.originalNodeObject.id, {
              unified_job_template: node.unifiedJobTemplate.id,
            })
          );
        }
      }
    });

    await Promise.all(nodeRequests);
    // Creating approval templates needs to happen after the node has been created
    // since we reference the node in the approval template request.
    await Promise.all(approvalTemplateRequests);
    const [linkMap, newLinks] = generateLinkMapAndNewLinks(originalLinkMap);
    await Promise.all(
      disassociateNodes(originalLinkMap, deletedNodeIds, linkMap)
    );
    await Promise.all(associateNodes(newLinks, originalLinkMap));

    history.push(`/templates/workflow_job_template/${template.id}/details`);
  };

  useEffect(() => {
    async function fetchData() {
      try {
        const workflowNodes = await fetchWorkflowNodes(template.id);
        dispatch({
          type: 'GENERATE_NODES_AND_LINKS',
          nodes: workflowNodes,
          i18n,
        });
      } catch (error) {
        dispatch({ type: 'SET_CONTENT_ERROR', value: error });
      } finally {
        dispatch({ type: 'SET_IS_LOADING', value: false });
      }
    }
    fetchData();
  }, [template.id, i18n]);

  // Update positions of nodes/links
  useEffect(() => {
    if (nodes) {
      const newNodePositions = {};
      const nonDeletedNodes = nodes.filter(node => !node.isDeleted);
      const g = layoutGraph(nonDeletedNodes, links);

      g.nodes().forEach(node => {
        newNodePositions[node] = g.node(node);
      });

      dispatch({ type: 'SET_NODE_POSITIONS', value: newNodePositions });
    }
  }, [links, nodes]);

  if (isLoading) {
    return (
      <CenteredContent>
        <ContentLoading />
      </CenteredContent>
    );
  }

  if (contentError) {
    return (
      <CenteredContent>
        <ContentError error={contentError} />
      </CenteredContent>
    );
  }

  const readOnly = !template?.summary_fields?.user_capabilities?.edit;

  return (
    <WorkflowStateContext.Provider value={state}>
      <WorkflowDispatchContext.Provider value={dispatch}>
        <Wrapper>
          <VisualizerToolbar
            onClose={handleVisualizerClose}
            onSave={handleVisualizerSave}
            hasUnsavedChanges={unsavedChanges}
            template={template}
            readOnly={readOnly}
          />
          {links.length > 0 ? (
            <VisualizerGraph readOnly={readOnly} />
          ) : (
            <VisualizerStartScreen readOnly={readOnly} />
          )}
        </Wrapper>
        {nodeToDelete && <NodeDeleteModal />}
        {linkToDelete && <LinkDeleteModal />}
        {linkToEdit && <LinkEditModal />}
        {addLinkSourceNode && addLinkTargetNode && <LinkAddModal />}
        {addNodeSource && <NodeAddModal />}
        {nodeToEdit && <NodeEditModal />}
        {showUnsavedChangesModal && (
          <UnsavedChangesModal
            onExit={() =>
              history.push(
                `/templates/workflow_job_template/${template.id}/details`
              )
            }
            onSaveAndExit={() => handleVisualizerSave()}
          />
        )}
        {showDeleteAllNodesModal && <DeleteAllNodesModal />}
        {nodeToView && <NodeViewModal readOnly={readOnly} />}
      </WorkflowDispatchContext.Provider>
    </WorkflowStateContext.Provider>
  );
}

Visualizer.propTypes = {
  template: shape().isRequired,
};

export default withI18n()(Visualizer);
