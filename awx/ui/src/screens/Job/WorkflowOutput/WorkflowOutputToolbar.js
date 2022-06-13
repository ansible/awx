import React, { useContext } from 'react';
import { useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import { shape } from 'prop-types';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';

import {
  CompassIcon,
  WrenchIcon,
  ProjectDiagramIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import StatusLabel from 'components/StatusLabel';
import JobCancelButton from 'components/JobCancelButton';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from 'contexts/Workflow';

const Toolbar = styled.div`
  align-items: center;
  border-bottom: 1px solid grey;
  display: flex;
  height: 56px;
`;

const ToolbarJob = styled.div`
  display: inline-flex;
  align-items: center;

  h1 {
    margin-right: 10px;
    font-weight: var(--pf-global--FontWeight--bold);
  }
`;

const ToolbarActions = styled.div`
  align-items: center;
  display: flex;
  flex: 1;
  justify-content: flex-end;
`;

const Badge = styled(PFBadge)`
  align-items: center;
  display: flex;
  justify-content: center;
  margin-left: 10px;
`;

const ActionButton = styled(Button)`
  border: none;
  margin: 0px 6px;
  padding: 6px 10px;
  &:hover {
    background-color: #0066cc;
    color: white;
  }

  &.pf-m-active {
    background-color: #0066cc;
    color: white;
  }
`;
function WorkflowOutputToolbar({ job }) {
  const dispatch = useContext(WorkflowDispatchContext);
  const history = useHistory();
  const { nodes, showLegend, showTools } = useContext(WorkflowStateContext);

  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;
  const navToWorkflow = () => {
    history.push(
      `/templates/workflow_job_template/${job.unified_job_template}/visualizer`
    );
  };
  return (
    <Toolbar id="workflow-output-toolbar" ouiaId="workflow-output-toolbar">
      <ToolbarJob>
        <h1>{job.name}</h1>
        <StatusLabel status={job.status} />
      </ToolbarJob>
      <ToolbarActions>
        {['new', 'pending', 'waiting', 'running'].includes(job?.status) &&
        job?.summary_fields?.user_capabilities?.start ? (
          <JobCancelButton
            style={{ margin: '0px 6px', padding: '6px 10px' }}
            job={job}
            errorTitle={t`Job Cancel Error`}
            title={t`Cancel ${job.name}`}
            errorMessage={t`Failed to cancel ${job.name}`}
            showIconButton
          />
        ) : null}

        <ActionButton
          ouiaId="edit-workflow"
          aria-label={t`Edit workflow`}
          id="edit-workflow"
          variant="plain"
          onClick={navToWorkflow}
        >
          <ProjectDiagramIcon />
        </ActionButton>
        <div>{t`Total Nodes`}</div>
        <Badge isRead>{totalNodes}</Badge>
        <Tooltip content={t`Toggle Legend`} position="bottom">
          <ActionButton
            id="workflow-output-toggle-legend"
            isActive={showLegend}
            onClick={() => dispatch({ type: 'TOGGLE_LEGEND' })}
            variant="plain"
          >
            <CompassIcon />
          </ActionButton>
        </Tooltip>
        <Tooltip content={t`Toggle Tools`} position="bottom">
          <ActionButton
            id="workflow-output-toggle-tools"
            isActive={showTools}
            onClick={() => dispatch({ type: 'TOGGLE_TOOLS' })}
            variant="plain"
          >
            <WrenchIcon />
          </ActionButton>
        </Tooltip>
      </ToolbarActions>
    </Toolbar>
  );
}

WorkflowOutputToolbar.propTypes = {
  job: shape().isRequired,
};

export default WorkflowOutputToolbar;
