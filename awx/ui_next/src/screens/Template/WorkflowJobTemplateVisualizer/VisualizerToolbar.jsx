import React, { useContext } from 'react';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '@contexts/Workflow';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { func, shape } from 'prop-types';
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
ActionButton.displayName = 'ActionButton';

function VisualizerToolbar({ i18n, onClose, onSave, template }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const { nodes, showLegend, showTools } = useContext(WorkflowStateContext);

  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <div id="visualizer-toolbar">
      <div css="align-items: center; border-bottom: 1px solid grey; display: flex; height: 56px; padding: 0px 20px;">
        <div css="display: flex;" id="visualizer-toolbar-template-name">
          <b>{template.name}</b>
        </div>
        <div css="align-items: center; display: flex; flex: 1; justify-content: flex-end">
          <div>{i18n._(t`Total Nodes`)}</div>
          <Badge id="visualizer-total-nodes-badge" isRead>
            {totalNodes}
          </Badge>
          <VerticalSeparator />
          <Tooltip content={i18n._(t`Toggle Legend`)} position="bottom">
            <ActionButton
              id="visualizer-toggle-legend"
              isActive={totalNodes > 0 && showLegend}
              isDisabled={totalNodes === 0}
              onClick={() => dispatch({ type: 'TOGGLE_LEGEND' })}
              variant="plain"
            >
              <CompassIcon />
            </ActionButton>
          </Tooltip>
          <Tooltip content={i18n._(t`Toggle Tools`)} position="bottom">
            <ActionButton
              id="visualizer-toggle-tools"
              isActive={totalNodes > 0 && showTools}
              isDisabled={totalNodes === 0}
              onClick={() => dispatch({ type: 'TOGGLE_TOOLS' })}
              variant="plain"
            >
              <WrenchIcon />
            </ActionButton>
          </Tooltip>
          <ActionButton
            id="visualizer-documentation"
            variant="plain"
            isDisabled
          >
            <BookIcon />
          </ActionButton>
          <ActionButton id="visualizer-launch" variant="plain" isDisabled>
            <RocketIcon />
          </ActionButton>
          <Tooltip content={i18n._(t`Delete All Nodes`)} position="bottom">
            <ActionButton
              id="visualizer-delete-all"
              aria-label={i18n._(t`Delete all nodes`)}
              isDisabled={totalNodes === 0}
              onClick={() =>
                dispatch({
                  type: 'SET_SHOW_DELETE_ALL_NODES_MODAL',
                  value: true,
                })
              }
              variant="plain"
            >
              <TrashAltIcon />
            </ActionButton>
          </Tooltip>
          <VerticalSeparator />
          <Button
            id="visualizer-save"
            aria-label={i18n._(t`Save`)}
            variant="primary"
            onClick={onSave}
          >
            {i18n._(t`Save`)}
          </Button>
          <VerticalSeparator />
          <Button
            id="visualizer-close"
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
  onClose: func.isRequired,
  onSave: func.isRequired,
  template: shape().isRequired,
};

export default withI18n()(VisualizerToolbar);
