import React, { useCallback, useEffect, useReducer } from 'react';
import { useHistory } from 'react-router-dom';

import styled from 'styled-components';
import { shape } from 'prop-types';
import { t } from '@lingui/macro';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';
import { getAddedAndRemoved } from 'util/lists';
import { stringIsUUID } from 'util/strings';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { layoutGraph } from 'components/Workflow/WorkflowUtils';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import workflowReducer from 'components/Workflow/workflowReducer';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import {
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from 'api';
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

const replaceIdentifier = (node) => {
  if (stringIsUUID(node.originalNodeObject.identifier) || node.identifier) {
    return true;
  }

  return false;
};
const getAggregatedCredentials = (
  originalNodeOverride = [],
  templateDefaultCredentials = []
) => {
  let theArray = [];

  const isCredentialOverriden = (templateDefaultCred) => {
    let credentialHasOverride = false;
    originalNodeOverride.forEach((overrideCred) => {
      if (
        templateDefaultCred.credential_type === overrideCred.credential_type
      ) {
        if (
          (!templateDefaultCred.vault_id && !overrideCred.inputs?.vault_id) ||
          (templateDefaultCred.vault_id &&
            overrideCred.inputs?.vault_id &&
            templateDefaultCred.vault_id === overrideCred.inputs?.vault_id)
        ) {
          credentialHasOverride = true;
        }
      }
    });

    return credentialHasOverride;
  };

  if (templateDefaultCredentials.length > 0) {
    templateDefaultCredentials.forEach((defaultCred) => {
      if (!isCredentialOverriden(defaultCred)) {
        theArray.push(defaultCred);
      }
    });
  }

  theArray = theArray.concat(originalNodeOverride);

  return theArray;
};

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

function Visualizer({ template }) {
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
    newLinks.forEach((link) => {
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
    Object.keys(originalLinkMap).forEach((key) => {
      const node = originalLinkMap[key];
      node.success_nodes.forEach((successNodeId) => {
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
      node.failure_nodes.forEach((failureNodeId) => {
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
      node.always_nodes.forEach((alwaysNodeId) => {
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

  useEffect(() => {
    async function fetchData() {
      try {
        const workflowNodes = await fetchWorkflowNodes(template.id);
        dispatch({
          type: 'GENERATE_NODES_AND_LINKS',
          nodes: workflowNodes,
        });
      } catch (error) {
        dispatch({ type: 'SET_CONTENT_ERROR', value: error });
      } finally {
        dispatch({ type: 'SET_IS_LOADING', value: false });
      }
    }
    fetchData();
  }, [template.id]);

  // Update positions of nodes/links
  useEffect(() => {
    if (nodes) {
      const newNodePositions = {};
      const nonDeletedNodes = nodes.filter((node) => !node.isDeleted);
      const g = layoutGraph(nonDeletedNodes, links);

      g.nodes().forEach((node) => {
        newNodePositions[node] = g.node(node);
      });

      dispatch({ type: 'SET_NODE_POSITIONS', value: newNodePositions });
    }
  }, [links, nodes]);

  const {
    error: saveVisualizerError,
    isLoading: isSavingVisualizer,
    request: saveVisualizer,
  } = useRequest(
    useCallback(async () => {
      const nodeRequests = [];
      const approvalTemplateRequests = [];
      const originalLinkMap = {};
      const deletedNodeIds = [];
      const associateCredentialRequests = [];
      const disassociateCredentialRequests = [];

      const generateLinkMapAndNewLinks = () => {
        const linkMap = {};
        const newLinks = [];

        links.forEach((link) => {
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

      nodes.forEach((node) => {
        // node with id=1 is the artificial start node
        if (node.id === 1) {
          return;
        }
        if (node.originalNodeObject && !node.isDeleted) {
          const { id, success_nodes, failure_nodes, always_nodes } =
            node.originalNodeObject;
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
          if (
            node.fullUnifiedJobTemplate.type === 'workflow_approval_template'
          ) {
            nodeRequests.push(
              WorkflowJobTemplatesAPI.createNode(template.id, {
                all_parents_must_converge: node.all_parents_must_converge,
                ...(node.identifier && { identifier: node.identifier }),
              }).then(({ data }) => {
                node.originalNodeObject = data;
                originalLinkMap[node.id] = {
                  id: data.id,
                  success_nodes: [],
                  failure_nodes: [],
                  always_nodes: [],
                };
                approvalTemplateRequests.push(
                  WorkflowJobTemplateNodesAPI.createApprovalTemplate(data.id, {
                    name: node.fullUnifiedJobTemplate.name,
                    description: node.fullUnifiedJobTemplate.description,
                    timeout: node.fullUnifiedJobTemplate.timeout,
                  })
                );
              })
            );
          } else {
            nodeRequests.push(
              WorkflowJobTemplatesAPI.createNode(template.id, {
                ...node.promptValues,
                inventory: node.promptValues?.inventory?.id || null,
                unified_job_template: node.fullUnifiedJobTemplate.id,
                all_parents_must_converge: node.all_parents_must_converge,
                ...(node.identifier && { identifier: node.identifier }),
              }).then(({ data }) => {
                node.originalNodeObject = data;
                originalLinkMap[node.id] = {
                  id: data.id,
                  success_nodes: [],
                  failure_nodes: [],
                  always_nodes: [],
                };

                if (node.promptValues?.addedCredentials?.length > 0) {
                  node.promptValues.addedCredentials.forEach((cred) => {
                    associateCredentialRequests.push(
                      WorkflowJobTemplateNodesAPI.associateCredentials(
                        data.id,
                        cred.id
                      )
                    );
                  });
                }
              })
            );
          }
        } else if (node.isEdited) {
          if (
            node.fullUnifiedJobTemplate.type === 'workflow_approval_template'
          ) {
            if (
              node.originalNodeObject.summary_fields.unified_job_template
                ?.unified_job_type === 'workflow_approval'
            ) {
              nodeRequests.push(
                WorkflowJobTemplateNodesAPI.replace(
                  node.originalNodeObject.id,
                  {
                    all_parents_must_converge: node.all_parents_must_converge,
                    ...(replaceIdentifier(node) && {
                      identifier: node.identifier,
                    }),
                  }
                ).then(({ data }) => {
                  node.originalNodeObject = data;
                  approvalTemplateRequests.push(
                    WorkflowApprovalTemplatesAPI.update(
                      node.originalNodeObject.summary_fields
                        .unified_job_template.id,
                      {
                        name: node.fullUnifiedJobTemplate.name,
                        description: node.fullUnifiedJobTemplate.description,
                        timeout: node.fullUnifiedJobTemplate.timeout,
                      }
                    )
                  );
                })
              );
            } else {
              nodeRequests.push(
                WorkflowJobTemplateNodesAPI.replace(
                  node.originalNodeObject.id,
                  {
                    all_parents_must_converge: node.all_parents_must_converge,
                    ...(replaceIdentifier(node) && {
                      identifier: node.identifier,
                    }),
                  }
                ).then(({ data }) => {
                  node.originalNodeObject = data;
                  approvalTemplateRequests.push(
                    WorkflowJobTemplateNodesAPI.createApprovalTemplate(
                      node.originalNodeObject.id,
                      {
                        name: node.fullUnifiedJobTemplate.name,
                        description: node.fullUnifiedJobTemplate.description,
                        timeout: node.fullUnifiedJobTemplate.timeout,
                      }
                    )
                  );
                })
              );
            }
          } else {
            nodeRequests.push(
              WorkflowJobTemplateNodesAPI.replace(node.originalNodeObject.id, {
                ...node.promptValues,
                inventory: node.promptValues?.inventory?.id || null,
                unified_job_template: node.fullUnifiedJobTemplate.id,
                all_parents_must_converge: node.all_parents_must_converge,
                ...(replaceIdentifier(node) && {
                  identifier: node.identifier,
                }),
              }).then(() => {
                const { added: addedCredentials, removed: removedCredentials } =
                  getAddedAndRemoved(
                    getAggregatedCredentials(
                      node?.originalNodeCredentials,
                      node.launchConfig?.defaults?.credentials
                    ),
                    node.promptValues?.credentials
                  );

                if (addedCredentials.length > 0) {
                  addedCredentials.forEach((cred) => {
                    associateCredentialRequests.push(
                      WorkflowJobTemplateNodesAPI.associateCredentials(
                        node.originalNodeObject.id,
                        cred.id
                      )
                    );
                  });
                }
                if (removedCredentials?.length > 0) {
                  removedCredentials.forEach((cred) =>
                    disassociateCredentialRequests.push(
                      WorkflowJobTemplateNodesAPI.disassociateCredentials(
                        node.originalNodeObject.id,
                        cred.id
                      )
                    )
                  );
                }
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

      await Promise.all(disassociateCredentialRequests);
      await Promise.all(associateCredentialRequests);

      history.push(`/templates/workflow_job_template/${template.id}/details`);
    }, [links, nodes, history, template.id]),
    {}
  );

  const { error: nodeRequestError, dismissError: dismissNodeRequestError } =
    useDismissableError(saveVisualizerError);

  if (isLoading || isSavingVisualizer) {
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
            onSave={() => saveVisualizer(nodes)}
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
            onSaveAndExit={() => saveVisualizer(nodes)}
          />
        )}
        {showDeleteAllNodesModal && <DeleteAllNodesModal />}
        {nodeToView && <NodeViewModal readOnly={readOnly} />}
        {nodeRequestError && (
          <AlertModal
            isOpen
            variant="error"
            title={t`Error saving the workflow!`}
            onClose={dismissNodeRequestError}
            aria-label={t`Error saving the workflow!`}
          >
            {t`There was an error saving the workflow.`}
            <ErrorDetail error={nodeRequestError} />
          </AlertModal>
        )}
      </WorkflowDispatchContext.Provider>
    </WorkflowStateContext.Provider>
  );
}

Visualizer.propTypes = {
  template: shape().isRequired,
};

export default Visualizer;
