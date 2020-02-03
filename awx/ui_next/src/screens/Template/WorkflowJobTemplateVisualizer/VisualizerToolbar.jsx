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

function VisualizerToolbar({ i18n, onClose, onSave, template }) {
  const dispatch = useContext(WorkflowDispatchContext);

  const { nodes, showLegend, showTools } = useContext(WorkflowStateContext);

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
          <Tooltip content={i18n._(t`Toggle Legend`)} position="bottom">
            <ActionButton
              isActive={showLegend}
              onClick={() => dispatch({ type: 'TOGGLE_LEGEND' })}
              variant="plain"
            >
              <CompassIcon />
            </ActionButton>
          </Tooltip>
          <Tooltip content={i18n._(t`Toggle Tools`)} position="bottom">
            <ActionButton
              isActive={showTools}
              onClick={() => dispatch({ type: 'TOGGLE_TOOLS' })}
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
            aria-label={i18n._(t`Save`)}
            variant="primary"
            onClick={onSave}
          >
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
  onClose: func.isRequired,
  onSave: func.isRequired,
  template: shape().isRequired,
};

export default withI18n()(VisualizerToolbar);
