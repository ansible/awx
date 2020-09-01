import 'styled-components/macro';
import React, { useContext } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { bool, func, shape } from 'prop-types';
import {
  Badge as PFBadge,
  Button,
  Title,
  Tooltip,
} from '@patternfly/react-core';
import {
  BookIcon,
  CompassIcon,
  RocketIcon,
  TimesIcon,
  TrashAltIcon,
  WrenchIcon,
} from '@patternfly/react-icons';
import styled from 'styled-components';
import LaunchButton from '../../../components/LaunchButton';
import {
  WorkflowDispatchContext,
  WorkflowStateContext,
} from '../../../contexts/Workflow';

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

const DOCLINK =
  'https://docs.ansible.com/ansible-tower/latest/html/userguide/workflow_templates.html#ug-wf-editor';

function VisualizerToolbar({
  i18n,
  onClose,
  onSave,
  template,
  hasUnsavedChanges,
  readOnly,
}) {
  const dispatch = useContext(WorkflowDispatchContext);

  const { nodes, showLegend, showTools } = useContext(WorkflowStateContext);

  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <div id="visualizer-toolbar">
      <div css="align-items: center; border-bottom: 1px solid grey; display: flex; height: 56px; padding: 0px 20px;">
        <Title
          headingLevel="h2"
          size="xl"
          id="visualizer-toolbar-template-name"
        >
          {template.name}
        </Title>
        <div css="align-items: center; display: flex; flex: 1; justify-content: flex-end">
          <div>{i18n._(t`Total Nodes`)}</div>
          <Badge id="visualizer-total-nodes-badge" isRead>
            {totalNodes}
          </Badge>
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
            aria-label={i18n._(t`Workflow Documentation`)}
            id="visualizer-documentation"
            variant="plain"
            component="a"
            target="_blank"
            href={DOCLINK}
          >
            <BookIcon />
          </ActionButton>
          {template.summary_fields?.user_capabilities?.start && (
            <LaunchButton resource={template} aria-label={i18n._(t`Launch`)}>
              {({ handleLaunch }) => (
                <ActionButton
                  id="visualizer-launch"
                  variant="plain"
                  isDisabled={hasUnsavedChanges || totalNodes === 0}
                  onClick={handleLaunch}
                >
                  <RocketIcon />
                </ActionButton>
              )}
            </LaunchButton>
          )}
          {!readOnly && (
            <>
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
              <Button
                id="visualizer-save"
                css="margin: 0 32px"
                aria-label={i18n._(t`Save`)}
                variant="primary"
                onClick={onSave}
              >
                {i18n._(t`Save`)}
              </Button>
            </>
          )}
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
  hasUnsavedChanges: bool.isRequired,
  readOnly: bool.isRequired,
};

export default withI18n()(VisualizerToolbar);
