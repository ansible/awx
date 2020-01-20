import React, { Fragment, useState, useEffect } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { shape } from 'prop-types';
import { BaseSizes, Title, TitleLevel } from '@patternfly/react-core';
import { layoutGraph } from '@util/workflow';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import {
  DeleteAllNodesModal,
  LinkModal,
  LinkDeleteModal,
  NodeDeleteModal,
  NodeViewModal,
  UnsavedChangesModal,
} from './Modals';
import { NodeModal } from './Modals/NodeModal';
import VisualizerGraph from './VisualizerGraph';
import VisualizerStartScreen from './VisualizerStartScreen';
import VisualizerToolbar from './VisualizerToolbar';
import {
  WorkflowApprovalTemplatesAPI,
  WorkflowJobTemplateNodesAPI,
  WorkflowJobTemplatesAPI,
} from '@api';

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

function Visualizer({ history, template, i18n }) {
  const [addLinkSourceNode, setAddLinkSourceNode] = useState(null);
  const [addLinkTargetNode, setAddLinkTargetNode] = useState(null);
  const [addNodeSource, setAddNodeSource] = useState(null);
  const [addNodeTarget, setAddNodeTarget] = useState(null);
  const [addingLink, setAddingLink] = useState(false);
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [linkToDelete, setLinkToDelete] = useState(null);
  const [linkToEdit, setLinkToEdit] = useState(null);
  const [links, setLinks] = useState([]);
  const [nextNodeId, setNextNodeId] = useState(0);
  const [nodePositions, setNodePositions] = useState(null);
  const [nodeToDelete, setNodeToDelete] = useState(null);
  const [nodeToEdit, setNodeToEdit] = useState(null);
  const [nodeToView, setNodeToView] = useState(null);
  const [nodes, setNodes] = useState([]);
  const [showDeleteAllNodesModal, setShowDeleteAllNodesModal] = useState(false);
  const [showKey, setShowKey] = useState(false);
  const [showTools, setShowTools] = useState(false);
  const [showUnsavedChangesModal, setShowUnsavedChangesModal] = useState(false);
  const [unsavedChanges, setUnsavedChanges] = useState(false);

  const startAddNode = (sourceNodeId, targetNodeId = null) => {
    setAddNodeSource(sourceNodeId);
    setAddNodeTarget(targetNodeId);
  };

  const finishAddingNode = newNode => {
    const newNodes = [...nodes];
    const newLinks = [...links];
    newNodes.push({
      id: nextNodeId,
      type: 'node',
      unifiedJobTemplate: newNode.nodeResource,
    });

    // Ensures that root nodes appear to always run
    // after "START"
    if (addNodeSource === 1) {
      newNode.linkType = 'always';
    }

    newLinks.push({
      source: { id: addNodeSource },
      target: { id: nextNodeId },
      linkType: newNode.linkType,
      type: 'link',
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
    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setAddNodeSource(null);
    setAddNodeTarget(null);
    setNextNodeId(nextNodeId + 1);
    setNodes(newNodes);
    setLinks(newLinks);
  };

  const startEditNode = node => {
    setNodeToEdit(node);
  };

  const finishEditingNode = editedNode => {
    const newNodes = [...nodes];
    const matchingNode = newNodes.find(node => node.id === nodeToEdit.id);
    matchingNode.unifiedJobTemplate = editedNode.nodeResource;
    matchingNode.isEdited = true;
    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setNodeToEdit(null);
    setNodes(newNodes);
  };

  const cancelNodeForm = () => {
    setAddNodeSource(null);
    setAddNodeTarget(null);
    setNodeToEdit(null);
  };

  const deleteNode = () => {
    const nodeId = nodeToDelete.id;
    const newNodes = [...nodes];
    const newLinks = [...links];

    newNodes.find(node => node.id === nodeToDelete.id).isDeleted = true;

    // Update the links
    const parents = [];
    const children = [];
    const linkParentMapping = {};

    // Remove any links that reference this node
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

    // Add the new links
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
              type: 'link',
            });
          }
        } else if (!linkParentMapping[child.id].includes(parentId)) {
          newLinks.push({
            source: { id: parentId },
            target: { id: child.id },
            linkType: child.linkType,
            type: 'link',
          });
        }
      });
    });
    // need to track that this node has been deleted if it's not new

    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setNodeToDelete(null);
    setNodes(newNodes);
    setLinks(newLinks);
  };

  const updateLink = linkType => {
    const newLinks = [...links];
    newLinks.forEach(link => {
      if (
        link.source.id === linkToEdit.source.id &&
        link.target.id === linkToEdit.target.id
      ) {
        link.linkType = linkType;
      }
    });

    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setLinkToEdit(null);
    setLinks(newLinks);
  };

  const startDeleteLink = link => {
    const parentMap = {};
    links.forEach(existingLink => {
      if (!parentMap[existingLink.target.id]) {
        parentMap[existingLink.target.id] = [];
      }
      parentMap[existingLink.target.id].push(existingLink.source.id);
    });

    link.isConvergenceLink = parentMap[link.target.id].length > 1;

    setLinkToDelete(link);
  };

  const deleteLink = () => {
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
        type: 'link',
      });
    }

    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setLinkToDelete(null);
    setLinks(newLinks);
  };

  const selectSourceNodeForLinking = sourceNode => {
    const newNodes = [...nodes];
    const parentMap = {};
    const invalidLinkTargetIds = [];
    // Find and mark any ancestors as disabled to prevent cycles
    links.forEach(link => {
      // id=1 is our artificial root node so we don't care about that
      if (link.source.id !== 1) {
        if (link.source.id === sourceNode.id) {
          // Disables direct children from the add link process
          invalidLinkTargetIds.push(link.target.id);
        }
        if (!parentMap[link.target.id]) {
          parentMap[link.target.id] = [];
        }
        parentMap[link.target.id].push(link.source.id);
      }
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

    setAddLinkSourceNode(sourceNode);
    setAddingLink(true);
    setNodes(newNodes);
  };

  const selectTargetNodeForLinking = targetNode => {
    setAddLinkTargetNode(targetNode);
  };

  const addLink = linkType => {
    const newLinks = [...links];
    const newNodes = [...nodes];

    newNodes.forEach(node => {
      node.isInvalidLinkTarget = false;
    });

    newLinks.push({
      source: { id: addLinkSourceNode.id },
      target: { id: addLinkTargetNode.id },
      linkType,
      type: 'link',
    });

    newLinks.forEach((link, index) => {
      if (link.source.id === 1 && link.target.id === addLinkTargetNode.id) {
        newLinks.splice(index, 1);
      }
    });

    if (!unsavedChanges) {
      setUnsavedChanges(true);
    }
    setAddLinkSourceNode(null);
    setAddLinkTargetNode(null);
    setAddingLink(false);
    setLinks(newLinks);
  };

  const cancelNodeLink = () => {
    const newNodes = [...nodes];

    newNodes.forEach(node => {
      node.isInvalidLinkTarget = false;
    });

    setAddLinkSourceNode(null);
    setAddLinkTargetNode(null);
    setAddingLink(false);
    setNodes(newNodes);
  };

  const deleteAllNodes = () => {
    setAddLinkSourceNode(null);
    setAddLinkTargetNode(null);
    setAddingLink(false);
    setNodes(
      nodes.map(node => {
        if (node.id !== 1) {
          node.isDeleted = true;
        }

        return node;
      })
    );
    setLinks([]);
    setShowDeleteAllNodesModal(false);
  };

  const handleVisualizerClose = () => {
    if (unsavedChanges) {
      setShowUnsavedChangesModal(true);
    } else {
      history.push(`/templates/workflow_job_template/${template.id}/details`);
    }
  };

  const handleVisualizerSave = async () => {
    const nodeRequests = [];
    const approvalTemplateRequests = [];
    const originalLinkMap = {};
    const deletedNodeIds = [];
    nodes.forEach(node => {
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
      if (node.id !== 1) {
        // node with id=1 is the artificial start node
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
                    WorkflowJobTemplateNodesAPI.createApprovalTemplate(
                      data.id,
                      {
                        name: node.unifiedJobTemplate.name,
                        description: node.unifiedJobTemplate.description,
                        timeout: node.unifiedJobTemplate.timeout,
                      }
                    )
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
                  node.originalNodeObject.summary_fields.unified_job_template
                    .id,
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
      }
    });

    await Promise.all(nodeRequests);
    await Promise.all(approvalTemplateRequests);

    const associateRequests = [];
    const disassociateRequests = [];
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

    Object.keys(originalLinkMap).forEach(key => {
      const node = originalLinkMap[key];
      node.success_nodes.forEach(successNodeId => {
        if (
          !deletedNodeIds.includes(successNodeId) &&
          (!linkMap[node.id] ||
            !linkMap[node.id][successNodeId] ||
            linkMap[node.id][successNodeId] !== 'success')
        ) {
          disassociateRequests.push(
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
          disassociateRequests.push(
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
          disassociateRequests.push(
            WorkflowJobTemplateNodesAPI.disassociateAlwaysNode(
              node.id,
              alwaysNodeId
            )
          );
        }
      });
    });

    await Promise.all(disassociateRequests);

    newLinks.forEach(link => {
      switch (link.linkType) {
        case 'success':
          associateRequests.push(
            WorkflowJobTemplateNodesAPI.associateSuccessNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        case 'failure':
          associateRequests.push(
            WorkflowJobTemplateNodesAPI.associateFailureNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        case 'always':
          associateRequests.push(
            WorkflowJobTemplateNodesAPI.associateAlwaysNode(
              originalLinkMap[link.source.id].id,
              originalLinkMap[link.target.id].id
            )
          );
          break;
        default:
      }
    });

    await Promise.all(associateRequests);

    // Some nodes (both new and edited) are going to need a followup request to
    // either create or update an approval job template.  This has to happen
    // after the node has been created
    history.push(`/templates/workflow_job_template/${template.id}/details`);
  };

  useEffect(() => {
    const buildGraphArrays = workflowNodes => {
      const allNodeIds = [];
      const arrayOfLinksForChart = [];
      const arrayOfNodesForChart = [
        {
          id: 1,
          unifiedJobTemplate: {
            name: i18n._(t`START`),
          },
          type: 'node',
        },
      ];
      const chartNodeIdToIndexMapping = {};
      const nodeIdToChartNodeIdMapping = {};
      const nonRootNodeIds = [];
      let nodeIdCounter = 2;
      // Assign each node an ID - 1 is reserved for the start node.  We need to
      // make sure that we have an ID on every node including new nodes so the
      // ID returned by the api won't do
      workflowNodes.forEach(node => {
        node.workflowMakerNodeId = nodeIdCounter;

        const nodeObj = {
          id: nodeIdCounter,
          type: 'node',
          originalNodeObject: node,
        };

        if (node.summary_fields.job) {
          nodeObj.job = node.summary_fields.job;
        }
        if (node.summary_fields.unified_job_template) {
          nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
        }

        arrayOfNodesForChart.push(nodeObj);
        allNodeIds.push(node.id);
        nodeIdToChartNodeIdMapping[node.id] = node.workflowMakerNodeId;
        chartNodeIdToIndexMapping[nodeIdCounter] = nodeIdCounter - 1;
        nodeIdCounter++;
      });

      workflowNodes.forEach(node => {
        const sourceIndex = chartNodeIdToIndexMapping[node.workflowMakerNodeId];
        node.success_nodes.forEach(nodeId => {
          const targetIndex =
            chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
          arrayOfLinksForChart.push({
            source: arrayOfNodesForChart[sourceIndex],
            target: arrayOfNodesForChart[targetIndex],
            linkType: 'success',
            type: 'link',
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
            type: 'link',
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
            type: 'link',
          });
          nonRootNodeIds.push(nodeId);
        });
      });

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
          type: 'link',
        });
      });

      setNodes(arrayOfNodesForChart);
      setLinks(arrayOfLinksForChart);
      setNextNodeId(nodeIdCounter);
    };

    async function fetchData() {
      try {
        const workflowNodes = await fetchWorkflowNodes(template.id);
        buildGraphArrays(workflowNodes);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
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

      setNodePositions(newNodePositions);
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

  return (
    <Fragment>
      <Wrapper>
        <VisualizerToolbar
          keyShown={showKey}
          nodes={nodes}
          onClose={handleVisualizerClose}
          onDeleteAllClick={() => setShowDeleteAllNodesModal(true)}
          onKeyToggle={() => setShowKey(!showKey)}
          onSave={handleVisualizerSave}
          onToolsToggle={() => setShowTools(!showTools)}
          template={template}
          toolsShown={showTools}
        />
        {links.length > 0 ? (
          <VisualizerGraph
            addLinkSourceNode={addLinkSourceNode}
            addingLink={addingLink}
            links={links}
            nodePositions={nodePositions}
            nodes={nodes}
            onAddNodeClick={startAddNode}
            onCancelAddLinkClick={cancelNodeLink}
            onConfirmAddLinkClick={selectTargetNodeForLinking}
            onDeleteLinkClick={startDeleteLink}
            onDeleteNodeClick={setNodeToDelete}
            onEditNodeClick={startEditNode}
            onLinkEditClick={setLinkToEdit}
            onStartAddLinkClick={selectSourceNodeForLinking}
            onViewNodeClick={setNodeToView}
            readOnly={!template.summary_fields.user_capabilities.edit}
            showKey={showKey}
            showTools={showTools}
          />
        ) : (
          <VisualizerStartScreen onStartClick={startAddNode} />
        )}
      </Wrapper>
      {nodeToDelete && (
        <NodeDeleteModal
          nodeToDelete={nodeToDelete}
          onCancel={() => setNodeToDelete(null)}
          onConfirm={deleteNode}
        />
      )}
      {linkToDelete && (
        <LinkDeleteModal
          linkToDelete={linkToDelete}
          onCancel={() => setLinkToDelete(null)}
          onConfirm={deleteLink}
        />
      )}
      {linkToEdit && (
        <LinkModal
          linkType={linkToEdit.linkType}
          header={
            <Title headingLevel={TitleLevel.h1} size={BaseSizes['2xl']}>
              {i18n._(t`Edit Link`)}
            </Title>
          }
          onCancel={() => setLinkToEdit(null)}
          onConfirm={updateLink}
        />
      )}
      {addLinkSourceNode && addLinkTargetNode && (
        <LinkModal
          header={
            <Title headingLevel={TitleLevel.h1} size={BaseSizes['2xl']}>
              {i18n._(t`Add Link`)}
            </Title>
          }
          onCancel={cancelNodeLink}
          onConfirm={addLink}
        />
      )}
      {addNodeSource && (
        <NodeModal
          askLinkType={addNodeSource !== 1}
          onClose={() => cancelNodeForm()}
          onSave={finishAddingNode}
          title={i18n._(t`Add Node`)}
        />
      )}
      {nodeToEdit && (
        <NodeModal
          askLinkType={false}
          nodeToEdit={nodeToEdit}
          onClose={() => cancelNodeForm()}
          onSave={finishEditingNode}
          title={i18n._(t`Edit Node`)}
        />
      )}
      {showUnsavedChangesModal && (
        <UnsavedChangesModal
          onCancel={() => setShowUnsavedChangesModal(false)}
          onExit={() =>
            history.push(
              `/templates/workflow_job_template/${template.id}/details`
            )
          }
          onSaveAndExit={() => handleVisualizerSave()}
        />
      )}
      {showDeleteAllNodesModal && (
        <DeleteAllNodesModal
          onCancel={() => setShowDeleteAllNodesModal(false)}
          onConfirm={() => deleteAllNodes()}
        />
      )}
      {nodeToView && (
        <NodeViewModal node={nodeToView} onClose={() => setNodeToView(null)} />
      )}
    </Fragment>
  );
}

Visualizer.propTypes = {
  template: shape().isRequired,
};

export default withI18n()(withRouter(Visualizer));
