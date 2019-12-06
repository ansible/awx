import React from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Badge as PFBadge, Button } from '@patternfly/react-core';
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

function Toolbar({ history, i18n, template }) {
  const handleVisualizerCancel = () => {
    history.push(`/templates/workflow_job_template/${template.id}/details`);
  };

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
          <Badge isRead>0</Badge>
          <VerticalSeparator />
          <Button variant="plain">
            <CompassIcon />
          </Button>
          <Button variant="plain">
            <WrenchIcon />
          </Button>
          <Button variant="plain">
            <DownloadIcon />
          </Button>
          <Button variant="plain">
            <BookIcon />
          </Button>
          <Button variant="plain">
            <RocketIcon />
          </Button>
          <Button variant="plain">
            <TrashAltIcon />
          </Button>
          <VerticalSeparator />
          <Button variant="primary" onClick={handleVisualizerCancel}>
            {i18n._(t`Save`)}
          </Button>
          <VerticalSeparator />
          <Button
            variant="plain"
            aria-label={i18n._(t`Close`)}
            onClick={handleVisualizerCancel}
          >
            <TimesIcon />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default withI18n()(withRouter(Toolbar));
