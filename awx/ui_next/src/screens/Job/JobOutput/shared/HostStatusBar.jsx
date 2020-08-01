import React from 'react';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Badge, Tooltip } from '@patternfly/react-core';

const BarWrapper = styled.div`
  background-color: #d7d7d7;
  display: flex;
  height: 5px;
  margin: 24px 0;
  width: 100%;
`;

const BarSegment = styled.div`
  background-color: ${props => props.color || 'inherit'};
  flex-grow: ${props => props.count || 0};
`;
BarSegment.displayName = 'BarSegment';

const TooltipContent = styled.div`
  align-items: center;
  display: flex;

  span.pf-c-badge {
    margin-left: 10px;
  }
`;

const HostStatusBar = ({ i18n, counts = {} }) => {
  const noData = Object.keys(counts).length === 0;
  const hostStatus = {
    ok: {
      color: '#4CB140',
      label: i18n._(t`OK`),
    },
    skipped: {
      color: '#73BCF7',
      label: i18n._(t`Skipped`),
    },
    changed: {
      color: '#F0AB00',
      label: i18n._(t`Changed`),
    },
    failures: {
      color: '#C9190B',
      label: i18n._(t`Failed`),
    },
    dark: {
      color: '#8F4700',
      label: i18n._(t`Unreachable`),
    },
  };

  const barSegments = Object.keys(hostStatus).map(key => {
    const count = counts[key] || 0;
    return (
      <Tooltip
        key={key}
        content={
          <TooltipContent>
            {hostStatus[key].label}
            <Badge isRead>{count}</Badge>
          </TooltipContent>
        }
      >
        <BarSegment key={key} color={hostStatus[key].color} count={count} />
      </Tooltip>
    );
  });

  if (noData) {
    return (
      <BarWrapper>
        <Tooltip
          content={i18n._(
            t`Host status information for this job is unavailable.`
          )}
        >
          <BarSegment count={1} />
        </Tooltip>
      </BarWrapper>
    );
  }

  return <BarWrapper>{barSegments}</BarWrapper>;
};

export default withI18n()(HostStatusBar);
