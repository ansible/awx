import React, { useEffect, useReducer } from 'react';
import { withI18n } from '@lingui/react';
import styled from 'styled-components';
import { shape } from 'prop-types';
import { CardBody as PFCardBody } from '@patternfly/react-core';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';
import { layoutGraph } from '../../../components/Workflow/WorkflowUtils';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import workflowReducer, {
  initReducer,
} from '../../../components/Workflow/workflowReducer';
import { WorkflowJobsAPI } from '../../../api';
import WorkflowOutputGraph from './WorkflowOutputGraph';
import WorkflowOutputToolbar from './WorkflowOutputToolbar';
import useWsWorkflowOutput from './useWsWorkflowOutput';

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
  const [state, dispatch] = useReducer(workflowReducer, {}, initReducer);
  const { contentError, isLoading, links, nodePositions, nodes } = state;

  useEffect(() => {
    async function fetchData() {
      try {
        const workflowNodes = await fetchWorkflowNodes(job.id);
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
    dispatch({ type: 'RESET' });
    fetchData();
  }, [job.id, i18n]);

  // Update positions of nodes/links
  useEffect(() => {
    if (nodes) {
      const newNodePositions = {};
      const g = layoutGraph(nodes, links);

      g.nodes().forEach(node => {
        newNodePositions[node] = g.node(node);
      });

      dispatch({ type: 'SET_NODE_POSITIONS', value: newNodePositions });
    }
  }, [job.id, links, nodes]);

  const updatedNodes = useWsWorkflowOutput(job.id, nodes);

  useEffect(() => {
    dispatch({ type: 'SET_NODES', value: updatedNodes });
  }, [updatedNodes]);

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
    <WorkflowStateContext.Provider value={state}>
      <WorkflowDispatchContext.Provider value={dispatch}>
        <CardBody>
          <Wrapper>
            <WorkflowOutputToolbar job={job} />
            {nodePositions && <WorkflowOutputGraph />}
          </Wrapper>
        </CardBody>
      </WorkflowDispatchContext.Provider>
    </WorkflowStateContext.Provider>
  );
}

WorkflowOutput.propTypes = {
  job: shape().isRequired,
};

export default withI18n()(WorkflowOutput);
