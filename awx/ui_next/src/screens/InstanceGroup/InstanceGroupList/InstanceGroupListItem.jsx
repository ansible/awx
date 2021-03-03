import React from 'react';
import { string, bool, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import 'styled-components/macro';
import {
  Button,
  Label,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
} from '@patternfly/react-core';
import { Tr, Td } from '@patternfly/react-table';
import { PencilAltIcon } from '@patternfly/react-icons';
import styled from 'styled-components';
import { ActionsTd, ActionItem } from '../../../components/PaginatedTable';
import { InstanceGroup } from '../../../types';

const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
`;

function InstanceGroupListItem({
  instanceGroup,
  detailUrl,
  isSelected,
  onSelect,
  rowIndex,
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
    <Tr id={`ig-row-${instanceGroup.id}`}>
      <Td
        select={{
          rowIndex,
          isSelected,
          onSelect,
        }}
        dataLabel={i18n._(t`Selected`)}
      />
      <Td id={labelId} dataLabel={i18n._(t`Name`)}>
        <Link to={`${detailUrl}`}>
          <b>{instanceGroup.name}</b>
          {verifyInstanceGroup(instanceGroup)}
        </Link>
      </Td>
      <Td dataLabel={i18n._(t`Type`)}>
        {isContainerGroup(instanceGroup)
          ? i18n._(t`Container group`)
          : i18n._(t`Instance group`)}
      </Td>
      <Td dataLabel={i18n._(t`Running jobs`)}>{instanceGroup.jobs_running}</Td>
      <Td dataLabel={i18n._(t`Total jobs`)}>{instanceGroup.jobs_total}</Td>
      <Td dataLabel={i18n._(t`Instances`)}>{instanceGroup.instances}</Td>
      <Td dataLabel={i18n._(t`Capacity`)}>{usedCapacity(instanceGroup)}</Td>
      <ActionsTd dataLabel={i18n._(t`Actions`)}>
        <ActionItem
          visible={instanceGroup.summary_fields.user_capabilities.edit}
          tooltip={i18n._(t`Edit instance group`)}
        >
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
        </ActionItem>
      </ActionsTd>
    </Tr>
  );
}
InstanceGroupListItem.prototype = {
  instanceGroup: InstanceGroup.isRequired,
  detailUrl: string.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default withI18n()(InstanceGroupListItem);
