import React from 'react';
import { bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import 'styled-components/macro';
import {
  Badge as PFBadge,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemRow,
  DataListItemCells,
} from '@patternfly/react-core';

import _DataListCell from '../../../components/DataListCell';
import InstanceToggle from '../../../components/InstanceToggle';
import { Instance } from '../../../types';

const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
`;

const DataListCell = styled(_DataListCell)`
  white-space: nowrap;
`;

const Badge = styled(PFBadge)`
  margin-left: 8px;
`;

const ListGroup = styled.span`
  margin-left: 12px;

  &:first-of-type {
    margin-left: 0;
  }
`;

function InstanceListItem({
  instance,
  isSelected,
  onSelect,
  fetchInstances,
  i18n,
}) {
  const labelId = `check-action-${instance.id}`;

  function usedCapacity(item) {
    if (item.enabled) {
      return (
        <Progress
          value={Math.round(100 - item.percent_capacity_remaining)}
          measureLocation={ProgressMeasureLocation.top}
          size={ProgressSize.sm}
          title={i18n._(t`Used capacity`)}
        />
      );
    }
    return <Unavailable>{i18n._(t`Unavailable`)}</Unavailable>;
  }

  return (
    <DataListItem
      aria-labelledby={labelId}
      id={`${instance.id}`}
      key={instance.id}
    >
      <DataListItemRow>
        <DataListCheck
          aria-labelledby={labelId}
          checked={isSelected}
          id={`instances-${instance.id}`}
          onChange={onSelect}
        />

        <DataListItemCells
          dataListCells={[
            <DataListCell key="name" aria-label={i18n._(t`instance host name`)}>
              <b>{instance.hostname}</b>
            </DataListCell>,
            <DataListCell key="type" aria-label={i18n._(t`instance type`)}>
              <b css="margin-right: 24px">{i18n._(t`Type`)}</b>
              <span id={labelId}>
                {instance.managed_by_policy
                  ? i18n._(t`Auto`)
                  : i18n._(t`Manual`)}
              </span>
            </DataListCell>,
            <DataListCell
              key="related-field-counts"
              aria-label={i18n._(t`instance counts`)}
              width={2}
            >
              <ListGroup>
                <b>{i18n._(t`Running jobs`)}</b>
                <Badge isRead>{instance.jobs_running}</Badge>
              </ListGroup>
              <ListGroup>
                <b>{i18n._(t`Total jobs`)}</b>
                <Badge isRead>{instance.jobs_total}</Badge>
              </ListGroup>
            </DataListCell>,
            <DataListCell
              key="capacity"
              aria-label={i18n._(t`instance group used capacity`)}
            >
              {usedCapacity(instance)}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          <InstanceToggle
            css="display: inline-flex;"
            fetchInstances={fetchInstances}
            instance={instance}
          />
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}
InstanceListItem.prototype = {
  instance: Instance.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InstanceListItem);
