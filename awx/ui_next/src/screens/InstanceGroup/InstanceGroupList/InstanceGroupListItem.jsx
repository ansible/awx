import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import 'styled-components/macro';
import {
  Badge as PFBadge,
  Button,
  DataListAction as _DataListAction,
  DataListCheck,
  DataListItem,
  DataListItemCells,
  DataListItemRow,
  Label,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  Tooltip,
} from '@patternfly/react-core';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import _DataListCell from '../../../components/DataListCell';
import { InstanceGroup } from '../../../types';

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

const DataListAction = styled(_DataListAction)`
  align-items: center;
  display: grid;
  grid-gap: 16px;
  grid-template-columns: 40px;
`;

const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
`;

function InstanceGroupListItem({
  instanceGroup,
  detailUrl,
  isSelected,
  onSelect,
  i18n,
}) {
  const labelId = `check-action-${instanceGroup.id}`;

  const isContainerGroup = item => {
    return item.is_containerized;
  };

  function usedCapacity(item) {
    if (!isContainerGroup(item)) {
      if (item.capacity) {
        return (
          <Progress
            value={Math.round(100 - item.percent_capacity_remaining)}
            measureLocation={ProgressMeasureLocation.top}
            size={ProgressSize.sm}
            title={i18n._(t`Used capacity`)}
          />
        );
      }
      return <Unavailable> {i18n._(t`Unavailable`)}</Unavailable>;
    }
    return null;
  }

  const verifyInstanceGroup = item => {
    if (item.is_isolated) {
      return (
        <span css="margin-left: 12px">
          <Label aria-label={i18n._(t`isolated instance`)}>
            {i18n._(t`Isolated`)}
          </Label>
        </span>
      );
    }
    if (item.is_controller) {
      return (
        <span css="margin-left: 12px">
          <Label aria-label={i18n._(t`controller instance`)}>
            {i18n._(t`Controller`)}
          </Label>
        </span>
      );
    }
    return null;
  };

  return (
    <DataListItem
      key={instanceGroup.id}
      aria-labelledby={labelId}
      id={`${instanceGroup.id} `}
    >
      <DataListItemRow>
        <DataListCheck
          id={`select-instance-groups-${instanceGroup.id}`}
          checked={isSelected}
          onChange={onSelect}
          aria-labelledby={labelId}
        />

        <DataListItemCells
          dataListCells={[
            <DataListCell
              key="name"
              aria-label={i18n._(t`instance group name`)}
            >
              <span id={labelId}>
                <Link to={`${detailUrl}`}>
                  <b>{instanceGroup.name}</b>
                </Link>
              </span>
              {verifyInstanceGroup(instanceGroup)}
            </DataListCell>,

            <DataListCell
              key="type"
              aria-label={i18n._(t`instance group type`)}
            >
              <b css="margin-right: 24px">{i18n._(t`Type`)}</b>
              <span id={labelId}>
                {isContainerGroup(instanceGroup)
                  ? i18n._(t`Container group`)
                  : i18n._(t`Instance group`)}
              </span>
            </DataListCell>,
            <DataListCell
              key="related-field-counts"
              aria-label={i18n._(t`instance counts`)}
              width={2}
            >
              <ListGroup>
                <b>{i18n._(t`Running jobs`)}</b>
                <Badge isRead>{instanceGroup.jobs_running}</Badge>
              </ListGroup>
              <ListGroup>
                <b>{i18n._(t`Total jobs`)}</b>
                <Badge isRead>{instanceGroup.jobs_total}</Badge>
              </ListGroup>

              {!instanceGroup.is_containerized ? (
                <ListGroup>
                  <b>{i18n._(t`Instances`)}</b>
                  <Badge isRead>{instanceGroup.instances}</Badge>
                </ListGroup>
              ) : null}
            </DataListCell>,

            <DataListCell
              key="capacity"
              aria-label={i18n._(t`instance group used capacity`)}
            >
              {usedCapacity(instanceGroup)}
            </DataListCell>,
          ]}
        />
        <DataListAction
          aria-label="actions"
          aria-labelledby={labelId}
          id={labelId}
        >
          {instanceGroup.summary_fields.user_capabilities.edit && (
            <Tooltip content={i18n._(t`Edit instance group`)} position="top">
              <Button
                aria-label={i18n._(t`Edit instance group`)}
                variant="plain"
                component={Link}
                to={
                  isContainerGroup(instanceGroup)
                    ? `/instance_groups/container_group/${instanceGroup.id}/edit`
                    : `/instance_groups/${instanceGroup.id}/edit`
                }
              >
                <PencilAltIcon />
              </Button>
            </Tooltip>
          )}
        </DataListAction>
      </DataListItemRow>
    </DataListItem>
  );
}
InstanceGroupListItem.prototype = {
  instanceGroup: InstanceGroup.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InstanceGroupListItem);
