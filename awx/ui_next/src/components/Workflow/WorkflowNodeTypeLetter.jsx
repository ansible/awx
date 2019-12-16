import React from 'react';
import styled from 'styled-components';
import { PauseIcon } from '@patternfly/react-icons';

const NodeTypeLetter = styled.foreignObject`
  font-size: 10px;
  color: white;
  text-align: center;
  line-height: 20px;
  background-color: #393f43;
  border-radius: 50%;
`;

function WorkflowNodeTypeLetter({ node }) {
  let nodeTypeLetter;
  if (node.unifiedJobTemplate && node.unifiedJobTemplate.type) {
    switch (node.unifiedJobTemplate.type) {
      case 'job_template':
        nodeTypeLetter = 'JT';
        break;
      case 'project':
        nodeTypeLetter = 'P';
        break;
      case 'inventory_source':
        nodeTypeLetter = 'I';
        break;
      case 'workflow_job_template':
        nodeTypeLetter = 'W';
        break;
      case 'workflow_approval_template':
        nodeTypeLetter = <PauseIcon />;
        break;
      default:
        nodeTypeLetter = '';
    }
  } else if (
    node.unifiedJobTemplate &&
    node.unifiedJobTemplate.unified_job_type
  ) {
    switch (node.unifiedJobTemplate.unified_job_type) {
      case 'job':
        nodeTypeLetter = 'JT';
        break;
      case 'project_update':
        nodeTypeLetter = 'P';
        break;
      case 'inventory_update':
        nodeTypeLetter = 'I';
        break;
      case 'workflow_job':
        nodeTypeLetter = 'W';
        break;
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

export default WorkflowNodeTypeLetter;
