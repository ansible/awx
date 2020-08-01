import React, { useContext } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { func, shape } from 'prop-types';
import { WorkflowStateContext } from '../../../contexts/Workflow';
import StatusIcon from '../../../components/StatusIcon';
import { WorkflowNodeTypeLetter } from '../../../components/Workflow';
import { secondsToHHMMSS } from '../../../util/dates';
import { constants as wfConstants } from '../../../components/Workflow/WorkflowUtils';

const NodeG = styled.g`
  cursor: ${props =>
    props.job && props.job.type !== 'workflow_approval'
      ? 'pointer'
      : 'default'};
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

Elapsed.displayName = 'Elapsed';

function WorkflowOutputNode({ i18n, mouseEnter, mouseLeave, node }) {
  const history = useHistory();
  const { nodePositions } = useContext(WorkflowStateContext);
  let borderColor = '#93969A';

  if (node.job) {
    if (
      node.job.status === 'failed' ||
      node.job.status === 'error' ||
      node.job.status === 'canceled'
    ) {
      borderColor = '#d9534f';
    }
    if (node.job.status === 'successful' || node.job.status === 'ok') {
      borderColor = '#5cb85c';
    }
  }

  const handleNodeClick = () => {
    if (node.job && node.job.type !== 'workflow_aproval') {
      history.push(`/jobs/${node.job.id}/details`);
    }
  };

  return (
    <NodeG
      id={`node-${node.id}`}
      transform={`translate(${nodePositions[node.id].x},${nodePositions[node.id]
        .y - nodePositions[1].y})`}
      job={node.job}
      onClick={handleNodeClick}
      onMouseEnter={mouseEnter}
      onMouseLeave={mouseLeave}
    >
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
          {node.job ? (
            <>
              <JobTopLine>
                {node.job.status && <StatusIcon status={node.job.status} />}
                <p>{node.job.name}</p>
              </JobTopLine>
              <Elapsed>{secondsToHHMMSS(node.job.elapsed)}</Elapsed>
            </>
          ) : (
            <NodeDefaultLabel>
              {node.unifiedJobTemplate
                ? node.unifiedJobTemplate.name
                : i18n._(t`DELETED`)}
            </NodeDefaultLabel>
          )}
        </NodeContents>
      </foreignObject>
      {(node.unifiedJobTemplate || node.job) && (
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

export default withI18n()(WorkflowOutputNode);
