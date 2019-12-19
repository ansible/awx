import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import Graph from './Graph';
import StartScreen from './StartScreen';
import Toolbar from './Toolbar';
import { WorkflowJobTemplatesAPI } from '@api';

const CenteredContent = styled.div`
  display: flex;
  flex-flow: column;
  height: 100%;
  align-items: center;
  justify-content: center;
`;

const VisualizerLayout = styled.div`
  display: flex;
  flex-flow: column;
  height: 100%;
`;

const fetchWorkflowNodes = async (templateId, pageNo = 1, nodes = []) => {
  try {
    const { data } = await WorkflowJobTemplatesAPI.readNodes(templateId, {
      page_size: 200,
      page: pageNo,
    });
    if (data.next) {
      return await fetchWorkflowNodes(
        templateId,
        pageNo + 1,
        nodes.concat(data.results)
      );
    }
    return nodes.concat(data.results);
  } catch (error) {
    throw error;
  }
};

function Visualizer({ template, i18n }) {
  const [contentError, setContentError] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [graphLinks, setGraphLinks] = useState([]);
  // We'll also need to store the original set of nodes...
  const [graphNodes, setGraphNodes] = useState([]);

  useEffect(() => {
    const buildGraphArrays = nodes => {
      const nonRootNodeIds = [];
      const allNodeIds = [];
      const arrayOfLinksForChart = [];
      const nodeIdToChartNodeIdMapping = {};
      const chartNodeIdToIndexMapping = {};
      const nodeRef = {};
      let nodeIdCounter = 1;
      const arrayOfNodesForChart = [
        {
          id: nodeIdCounter,
          unifiedJobTemplate: {
            name: i18n._(t`START`),
          },
          type: 'node',
        },
      ];
      nodeIdCounter++;
      // Assign each node an ID - 0 is reserved for the start node.  We need to
      // make sure that we have an ID on every node including new nodes so the
      // ID returned by the api won't do
      nodes.forEach(node => {
        node.workflowMakerNodeId = nodeIdCounter;
        nodeRef[nodeIdCounter] = {
          originalNodeObject: node,
        };

        const nodeObj = {
          index: nodeIdCounter - 1,
          id: nodeIdCounter,
          type: 'node',
        };

        if (node.summary_fields.job) {
          nodeObj.job = node.summary_fields.job;
        }
        if (node.summary_fields.unified_job_template) {
          nodeRef[nodeIdCounter].unifiedJobTemplate =
            node.summary_fields.unified_job_template;
          nodeObj.unifiedJobTemplate = node.summary_fields.unified_job_template;
        }

        arrayOfNodesForChart.push(nodeObj);
        allNodeIds.push(node.id);
        nodeIdToChartNodeIdMapping[node.id] = node.workflowMakerNodeId;
        chartNodeIdToIndexMapping[nodeIdCounter] = nodeIdCounter - 1;
        nodeIdCounter++;
      });

      nodes.forEach(node => {
        const sourceIndex = chartNodeIdToIndexMapping[node.workflowMakerNodeId];
        node.success_nodes.forEach(nodeId => {
          const targetIndex =
            chartNodeIdToIndexMapping[nodeIdToChartNodeIdMapping[nodeId]];
          arrayOfLinksForChart.push({
            source: arrayOfNodesForChart[sourceIndex],
            target: arrayOfNodesForChart[targetIndex],
            edgeType: 'success',
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
            edgeType: 'failure',
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
            edgeType: 'always',
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
          edgeType: 'always',
          type: 'link',
        });
      });

      setGraphNodes(arrayOfNodesForChart);
      setGraphLinks(arrayOfLinksForChart);
    };

    async function fetchData() {
      try {
        const nodes = await fetchWorkflowNodes(template.id);
        buildGraphArrays(nodes);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [template.id, i18n]);

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
    <VisualizerLayout>
      <Toolbar template={template} />
      {graphLinks.length > 0 ? (
        <Graph
          links={graphLinks}
          nodes={graphNodes}
          readOnly={!template.summary_fields.user_capabilities.edit}
        />
      ) : (
        <StartScreen />
      )}
    </VisualizerLayout>
  );
}

export default withI18n()(Visualizer);
