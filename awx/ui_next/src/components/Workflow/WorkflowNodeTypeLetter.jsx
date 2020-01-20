import React from 'react';
import styled from 'styled-components';
import { shape } from 'prop-types';
import { PauseIcon } from '@patternfly/react-icons';

const NodeTypeLetter = styled.foreignObject`
  background-color: #393f43;
  border-radius: 50%;
  color: white;
  font-size: 10px;
  line-height: 20px;
  text-align: center;
`;

function WorkflowNodeTypeLetter({ node }) {
  let nodeTypeLetter;
  if (
    node.unifiedJobTemplate &&
    (node.unifiedJobTemplate.type || node.unifiedJobTemplate.unified_job_type)
  ) {
    const ujtType =
      node.unifiedJobTemplate.type || node.unifiedJobTemplate.unified_job_type;
    switch (ujtType) {
      case 'job_template':
      case 'job':
        nodeTypeLetter = 'JT';
        break;
      case 'project':
      case 'project_update':
        nodeTypeLetter = 'P';
        break;
      case 'inventory_source':
      case 'inventory_update':
        nodeTypeLetter = 'I';
        break;
      case 'workflow_job_template':
      case 'workflow_job':
        nodeTypeLetter = 'W';
        break;
      case 'workflow_approval_template':
      case 'workflow_approval':
        nodeTypeLetter = <PauseIcon />;
        break;
      default:
        nodeTypeLetter = '';
    }
  }

  return (
    <NodeTypeLetter y="50" x="-10" height="20" width="20">
      {nodeTypeLetter}
    </NodeTypeLetter>
  );
}

WorkflowNodeTypeLetter.propTypes = {
  node: shape().isRequired,
};

export default WorkflowNodeTypeLetter;
