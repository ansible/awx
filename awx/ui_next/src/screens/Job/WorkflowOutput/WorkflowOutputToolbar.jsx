import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { arrayOf, bool, func, shape } from 'prop-types';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import { CompassIcon, WrenchIcon } from '@patternfly/react-icons';
import { StatusIcon } from '@components/Sparkline';
import VerticalSeparator from '@components/VerticalSeparator';
import styled from 'styled-components';

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

function WorkflowOutputToolbar({
  i18n,
  job,
  keyShown,
  nodes,
  onKeyToggle,
  onToolsToggle,
  toolsShown,
}) {
  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <div css="border-bottom: 1px solid grey; height: 56px; display: flex; alignItems: center">
      <div css="display: flex; align-items: center;">
        <StatusIcon status={job.status} css="margin-right: 20px" />
        <b>{job.name}</b>
      </div>
      <div css="display: flex; flex: 1; justify-content: flex-end; align-items: center;">
        <div>{i18n._(t`Total Nodes`)}</div>
        <Badge isRead>{totalNodes}</Badge>
        <VerticalSeparator />
        <Tooltip content={i18n._(t`Toggle Key`)} position="bottom">
          <ActionButton
            isActive={keyShown}
            onClick={onKeyToggle}
            variant="plain"
          >
            <CompassIcon />
          </ActionButton>
        </Tooltip>
        <Tooltip content={i18n._(t`Toggle Tools`)} position="bottom">
          <ActionButton
            isActive={toolsShown}
            onClick={onToolsToggle}
            variant="plain"
          >
            <WrenchIcon />
          </ActionButton>
        </Tooltip>
      </div>
    </div>
  );
}

WorkflowOutputToolbar.propTypes = {
  job: shape().isRequired,
  keyShown: bool.isRequired,
  nodes: arrayOf(shape()),
  onKeyToggle: func.isRequired,
  onToolsToggle: func.isRequired,
  toolsShown: bool.isRequired,
};

WorkflowOutputToolbar.defaultProps = {
  nodes: [],
};

export default withI18n()(WorkflowOutputToolbar);
