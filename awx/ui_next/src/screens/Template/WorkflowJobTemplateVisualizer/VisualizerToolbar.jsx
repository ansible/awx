import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { arrayOf, bool, func, shape } from 'prop-types';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import {
  BookIcon,
  CompassIcon,
  RocketIcon,
  TimesIcon,
  TrashAltIcon,
  WrenchIcon,
} from '@patternfly/react-icons';
import VerticalSeparator from '@components/VerticalSeparator';
import styled from 'styled-components';

const Badge = styled(PFBadge)`
  align-items: center;
  display: flex;
  justify-content: center;
  margin-left: 10px;
`;

const ActionButton = styled(Button)`
  padding: 6px 10px;
  margin: 0px 6px;
  border: none;
  &:hover {
    background-color: #0066cc;
    color: white;
  }

  &.pf-m-active {
    background-color: #0066cc;
    color: white;
  }
`;

function VisualizerToolbar({
  i18n,
  keyShown,
  nodes,
  onClose,
  onDeleteAllClick,
  onKeyToggle,
  onSave,
  onToolsToggle,
  template,
  toolsShown,
}) {
  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <div>
      <div css="align-items: center; border-bottom: 1px solid grey; display: flex; height: 56px; padding: 0px 20px;">
        <div css="display: flex;">
          <b>{i18n._(t`Workflow Visualizer`)}</b>
          <VerticalSeparator />
          <b>{template.name}</b>
        </div>
        <div css="align-items: center; display: flex; flex: 1; justify-content: flex-end">
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
          <ActionButton variant="plain" isDisabled>
            <BookIcon />
          </ActionButton>
          <ActionButton variant="plain" isDisabled>
            <RocketIcon />
          </ActionButton>
          <Tooltip content={i18n._(t`Delete All Nodes`)} position="bottom">
            <ActionButton
              aria-label={i18n._(t`Delete all nodes`)}
              isDisabled={totalNodes === 0}
              onClick={onDeleteAllClick}
              variant="plain"
            >
              <TrashAltIcon />
            </ActionButton>
          </Tooltip>
          <VerticalSeparator />
          <Button variant="primary" onClick={onSave}>
            {i18n._(t`Save`)}
          </Button>
          <VerticalSeparator />
          <Button
            aria-label={i18n._(t`Close`)}
            onClick={onClose}
            variant="plain"
          >
            <TimesIcon />
          </Button>
        </div>
      </div>
    </div>
  );
}

VisualizerToolbar.propTypes = {
  keyShown: bool.isRequired,
  nodes: arrayOf(shape()),
  onClose: func.isRequired,
  onDeleteAllClick: func.isRequired,
  onKeyToggle: func.isRequired,
  onSave: func.isRequired,
  onToolsToggle: func.isRequired,
  template: shape().isRequired,
  toolsShown: bool.isRequired,
};

VisualizerToolbar.defaultProps = {
  nodes: [],
};

export default withI18n()(VisualizerToolbar);
