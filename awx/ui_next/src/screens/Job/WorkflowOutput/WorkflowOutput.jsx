import React, { useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { shape } from 'prop-types';
import { CardBody as PFCardBody } from '@patternfly/react-core';
import { layoutGraph } from '@util/workflow';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { WorkflowJobsAPI } from '@api';
import WorkflowOutputGraph from './WorkflowOutputGraph';
import WorkflowOutputToolbar from './WorkflowOutputToolbar';

const CardBody = styled(PFCardBody)`
  display: flex;
  flex-direction: column;
  height: calc(100vh - 240px);
`;

const Wrapper = styled.div`
  display: flex;
  flex-flow: column;
  height: 100%;
  position: relative;
`;

const fetchWorkflowNodes = async (jobId, pageNo = 1, nodes = []) => {
  const { data } = await WorkflowJobsAPI.readNodes(jobId, {
    page_size: 200,
    page: pageNo,
  });
  if (data.next) {
    return fetchWorkflowNodes(jobId, pageNo + 1, nodes.concat(data.results));
  }
  return nodes.concat(data.results);
};

function WorkflowOutput({ job, i18n }) {
  const [contentError, setContentError] = useState(null);
  const [graphLinks, setGraphLinks] = useState([]);
  const [graphNodes, setGraphNodes] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [nodePositions, setNodePositions] = useState(null);
  const [showKey, setShowKey] = useState(false);
  const [showTools, setShowTools] = useState(false);

  useEffect(() => {
    const buildGraphArrays = nodes => {
      const allNodeIds = [];
      const arrayOfLinksForChart = [];
      const chartNodeIdToIndexMapping = {};
      const nodeIdToChartNodeIdMapping = {};
      const nodeRef = {};
      const nonRootNodeIds = [];
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

      setGraphNodes(arrayOfNodesForChart);
      setGraphLinks(arrayOfLinksForChart);
    };

    async function fetchData() {
      try {
        const nodes = await fetchWorkflowNodes(job.id);
        buildGraphArrays(nodes);
      } catch (error) {
        setContentError(error);
      } finally {
        setIsLoading(false);
      }
    }
    fetchData();
  }, [job.id, job.unified_job_template, i18n]);

  // Update positions of nodes/links
  useEffect(() => {
    if (graphNodes) {
      const newNodePositions = {};
      const g = layoutGraph(graphNodes, graphLinks);

      g.nodes().forEach(node => {
        newNodePositions[node] = g.node(node);
      });

      setNodePositions(newNodePositions);
    }
  }, [graphLinks, graphNodes]);

  if (isLoading) {
    return (
      <CardBody>
        <ContentLoading />
      </CardBody>
    );
  }

  if (contentError) {
    return (
      <CardBody>
        <ContentError error={contentError} />
      </CardBody>
    );
  }

  return (
    <CardBody>
      <Wrapper>
        <WorkflowOutputToolbar
          job={job}
          keyShown={showKey}
          nodes={graphNodes}
          onKeyToggle={() => setShowKey(!showKey)}
          onToolsToggle={() => setShowTools(!showTools)}
          toolsShown={showTools}
        />
        {nodePositions && (
          <WorkflowOutputGraph
            links={graphLinks}
            nodePositions={nodePositions}
            nodes={graphNodes}
            showKey={showKey}
            showTools={showTools}
          />
        )}
      </Wrapper>
    </CardBody>
  );
}

WorkflowOutput.propTypes = {
  job: shape().isRequired,
};

export default withI18n()(WorkflowOutput);
