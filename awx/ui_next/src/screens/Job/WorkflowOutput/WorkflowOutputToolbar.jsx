import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { shape } from 'prop-types';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import { CompassIcon, WrenchIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import StatusIcon from '../../../components/StatusIcon';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';

const Toolbar = styled.div`
  align-items: center;
  border-bottom: 1px solid grey;
  display: flex;
  height: 56px;
`;

const ToolbarJob = styled.div`
  align-items: center;
  display: flex;
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

const StatusIconWithMargin = styled(StatusIcon)`
  margin-right: 20px;
`;

function WorkflowOutputToolbar({ i18n, job }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const { nodes, showLegend, showTools } = useContext(WorkflowStateContext);

  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <Toolbar id="workflow-output-toolbar">
      <ToolbarJob>
        <StatusIconWithMargin status={job.status} />
        <b>{job.name}</b>
      </ToolbarJob>
      <ToolbarActions>
        <div>{i18n._(t`Total Nodes`)}</div>
        <Badge isRead>{totalNodes}</Badge>
        <Tooltip content={i18n._(t`Toggle Legend`)} position="bottom">
          <ActionButton
            id="workflow-output-toggle-legend"
            isActive={showLegend}
            onClick={() => dispatch({ type: 'TOGGLE_LEGEND' })}
            variant="plain"
          >
            <CompassIcon />
          </ActionButton>
        </Tooltip>
        <Tooltip content={i18n._(t`Toggle Tools`)} position="bottom">
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

export default withI18n()(WorkflowOutputToolbar);
