import React, { Fragment } from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { func, shape } from 'prop-types';
import { StatusIcon } from '@components/Sparkline';
import { WorkflowNodeTypeLetter } from '@components/Workflow';
import { secondsToHHMMSS } from '@util/dates';
import { constants as wfConstants } from '@util/workflow';

const NodeG = styled.g`
  cursor: ${props => (props.job ? 'pointer' : 'default')};
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

const NodeContents = styled.foreignObject`
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

function WorkflowOutputNode({
  history,
  i18n,
  mouseEnter,
  mouseLeave,
  node,
  nodePositions,
}) {
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
    if (node.job) {
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
      <NodeContents height="60" width="180">
        {node.job ? (
          <Fragment>
            <JobTopLine>
              <StatusIcon status={node.job.status} />
              <p>
                {node.unifiedJobTemplate
                  ? node.unifiedJobTemplate.name
                  : i18n._(t`DELETED`)}
              </p>
            </JobTopLine>
            <Elapsed>
              <span>{secondsToHHMMSS(node.job.elapsed)}</span>
            </Elapsed>
          </Fragment>
        ) : (
          <NodeDefaultLabel>
            {node.unifiedJobTemplate
              ? node.unifiedJobTemplate.name
              : i18n._(t`DELETED`)}
          </NodeDefaultLabel>
        )}
      </NodeContents>
      <circle cy="60" r="10" fill="#393F43" />
      {node.unifiedJobTemplate && <WorkflowNodeTypeLetter node={node} />}
    </NodeG>
  );
}

WorkflowOutputNode.propTypes = {
  mouseEnter: func.isRequired,
  mouseLeave: func.isRequired,
  node: shape().isRequired,
  nodePositions: shape().isRequired,
};

export default withI18n()(withRouter(WorkflowOutputNode));
