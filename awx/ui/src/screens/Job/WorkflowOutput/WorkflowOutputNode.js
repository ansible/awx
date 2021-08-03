import React, { useContext } from 'react';
import { useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';
import styled from 'styled-components';
import { func, shape } from 'prop-types';
import { WorkflowStateContext } from 'contexts/Workflow';
import StatusIcon from 'components/StatusIcon';
import { WorkflowNodeTypeLetter } from 'components/Workflow';
import { secondsToHHMMSS } from 'util/dates';
import { stringIsUUID } from 'util/strings';
import { constants as wfConstants } from 'components/Workflow/WorkflowUtils';

const NodeG = styled.g`
  cursor: ${(props) => (props.job ? 'pointer' : 'default')};
`;

const JobTopLine = styled.div`
  align-items: center;
  display: flex;
  margin-top: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  p {
    margin-left: 10px;
    white-space: nowrap;
    text-overflow: ellipsis;
    overflow: hidden;
  }
`;

const Elapsed = styled.div`
  margin-top: 5px;
  text-align: center;

  span {
    font-size: 12px;
    font-weight: bold;
    background-color: #ededed;
    padding: 3px 12px;
    border-radius: 14px;
  }
`;

const NodeContents = styled.div`
  font-size: 13px;
  padding: 0px 10px;
`;

const NodeDefaultLabel = styled.p`
  margin-top: 20px;
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const ConvergenceLabel = styled.p`
  font-size: 12px;
  color: #ffffff;
`;

Elapsed.displayName = 'Elapsed';

function WorkflowOutputNode({ mouseEnter, mouseLeave, node }) {
  const history = useHistory();
  const { nodePositions } = useContext(WorkflowStateContext);
  const job = node?.originalNodeObject?.summary_fields?.job;

  let borderColor = '#93969A';

  if (job) {
    if (
      job.status === 'failed' ||
      job.status === 'error' ||
      job.status === 'canceled'
    ) {
      borderColor = '#d9534f';
    }
    if (job.status === 'successful' || job.status === 'ok') {
      borderColor = '#5cb85c';
    }
  }

  const handleNodeClick = () => {
    if (job) {
      const basePath =
        job.type !== 'workflow_approval' ? 'jobs' : 'workflow_approvals';
      history.push(`/${basePath}/${job.id}/details`);
    }
  };

  let nodeName;

  if (
    node?.identifier ||
    (node?.originalNodeObject?.identifier &&
      !stringIsUUID(node.originalNodeObject.identifier))
  ) {
    nodeName = node?.identifier
      ? node?.identifier
      : node?.originalNodeObject?.identifier;
  } else {
    nodeName =
      node?.fullUnifiedJobTemplate?.name ||
      node?.originalNodeObject?.summary_fields?.unified_job_template?.name ||
      t`DELETED`;
  }

  return (
    <NodeG
      id={`node-${node.id}`}
      transform={`translate(${nodePositions[node.id].x},${
        nodePositions[node.id].y - nodePositions[1].y
      })`}
      job={job}
      onClick={handleNodeClick}
      onMouseEnter={mouseEnter}
      onMouseLeave={mouseLeave}
    >
      {(node.all_parents_must_converge ||
        node?.originalNodeObject?.all_parents_must_converge) && (
        <>
          <rect
            fill={borderColor}
            height={wfConstants.nodeH / 4}
            rx={2}
            ry={2}
            x={wfConstants.nodeW / 2 - wfConstants.nodeW / 10}
            y={-wfConstants.nodeH / 4 + 2}
            stroke={borderColor}
            strokeWidth="2px"
            width={wfConstants.nodeW / 5}
          />
          <foreignObject
            height={wfConstants.nodeH / 4}
            width={wfConstants.nodeW / 5}
            x={wfConstants.nodeW / 2 - wfConstants.nodeW / 10 + 7}
            y={-wfConstants.nodeH / 4 - 1}
          >
            <ConvergenceLabel>{t`ALL`}</ConvergenceLabel>
          </foreignObject>
        </>
      )}
      <rect
        fill="#FFFFFF"
        height={wfConstants.nodeH}
        rx="2"
        ry="2"
        stroke={borderColor}
        strokeWidth="2px"
        width={wfConstants.nodeW}
      />
      <foreignObject height="58" width="178" x="1" y="1">
        <NodeContents>
          {job ? (
            <>
              <JobTopLine>
                {job.status !== 'pending' && <StatusIcon status={job.status} />}
                <p>{nodeName}</p>
              </JobTopLine>
              {!!job?.elapsed && (
                <Elapsed>{secondsToHHMMSS(job.elapsed)}</Elapsed>
              )}
            </>
          ) : (
            <NodeDefaultLabel>{nodeName}</NodeDefaultLabel>
          )}
        </NodeContents>
      </foreignObject>
      {(node.unifiedJobTemplate || job) && (
        <WorkflowNodeTypeLetter node={node} />
      )}
    </NodeG>
  );
}

WorkflowOutputNode.propTypes = {
  mouseEnter: func.isRequired,
  mouseLeave: func.isRequired,
  node: shape().isRequired,
};

export default WorkflowOutputNode;
