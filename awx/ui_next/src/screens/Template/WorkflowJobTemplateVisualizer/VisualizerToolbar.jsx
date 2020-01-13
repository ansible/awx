import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Badge as PFBadge, Button, Tooltip } from '@patternfly/react-core';
import {
  BookIcon,
  CompassIcon,
  DownloadIcon,
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

function Toolbar({
  i18n,
  template,
  onClose,
  onSave,
  nodes = [],
  onDeleteAllClick,
  onKeyToggle,
  keyShown,
  onToolsToggle,
  toolsShown,
}) {
  const totalNodes = nodes.reduce((n, node) => n + !node.isDeleted, 0) - 1;

  return (
    <div>
      <div
        style={{
          borderBottom: '1px solid grey',
          height: '56px',
          display: 'flex',
          alignItems: 'center',
          padding: '0px 20px',
        }}
      >
        <div style={{ display: 'flex' }}>
          <b>{i18n._(t`Workflow Visualizer`)}</b>
          <VerticalSeparator />
          <b>{template.name}</b>
        </div>
        <div
          style={{
            display: 'flex',
            flex: '1',
            justifyContent: 'flex-end',
            alignItems: 'center',
          }}
        >
          <div>{i18n._(t`Total Nodes`)}</div>
          <Badge isRead>{totalNodes}</Badge>
          <VerticalSeparator />
          <Tooltip content={i18n._(t`Toggle Key`)} position="bottom">
            <ActionButton
              variant="plain"
              onClick={onKeyToggle}
              isActive={keyShown}
            >
              <CompassIcon />
            </ActionButton>
          </Tooltip>
          <Tooltip content={i18n._(t`Toggle Tools`)} position="bottom">
            <ActionButton
              variant="plain"
              onClick={onToolsToggle}
              isActive={toolsShown}
            >
              <WrenchIcon />
            </ActionButton>
          </Tooltip>
          <ActionButton variant="plain" isDisabled>
            <DownloadIcon />
          </ActionButton>
          <ActionButton variant="plain" isDisabled>
            <BookIcon />
          </ActionButton>
          <ActionButton variant="plain" isDisabled>
            <RocketIcon />
          </ActionButton>
          <Tooltip content={i18n._(t`Delete All Nodes`)} position="bottom">
            <ActionButton
              variant="plain"
              isDisabled={totalNodes === 0}
              aria-label={i18n._(t`Delete all nodes`)}
              onClick={onDeleteAllClick}
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
            variant="plain"
            aria-label={i18n._(t`Close`)}
            onClick={onClose}
          >
            <TimesIcon />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default withI18n()(Toolbar);
