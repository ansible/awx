import React, { useState, useCallback } from 'react';
import { bool, func } from 'prop-types';
import { t, Plural } from '@lingui/macro';
import styled from 'styled-components';
import 'styled-components/macro';
import {
  Badge as PFBadge,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  DataListAction as PFDataListAction,
  DataListCheck,
  DataListItem as PFDataListItem,
  DataListItemRow as PFDataListItemRow,
  DataListItemCells as PFDataListItemCells,
  Slider,
} from '@patternfly/react-core';

import _DataListCell from '../../../components/DataListCell';
import InstanceToggle from '../../../components/InstanceToggle';
import { Instance } from '../../../types';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import useDebounce from '../../../util/useDebounce';
import { InstancesAPI } from '../../../api';
import { useConfig } from '../../../contexts/Config';
import AlertModal from '../../../components/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail';

const DataListItem = styled(PFDataListItem)`
  display: flex;
  flex-direction: column;
  justify-content: center;
`;

const DataListItemRow = styled(PFDataListItemRow)`
  align-items: center;
`;

const DataListItemCells = styled(PFDataListItemCells)`
  align-items: center;
`;

const DataListAction = styled(PFDataListAction)`
  align-items: center;
`;
const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
`;

const DataListCell = styled(_DataListCell)`
  white-space: nowrap;
  align-items: center;
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

const SliderHolder = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const SliderForks = styled.div`
  flex-grow: 1;
  margin-right: 8px;
  margin-left: 8px;
  text-align: center;
`;

function computeForks(memCapacity, cpuCapacity, selectedCapacityAdjustment) {
  const minCapacity = Math.min(memCapacity, cpuCapacity);
  const maxCapacity = Math.max(memCapacity, cpuCapacity);

  return Math.floor(
    minCapacity + (maxCapacity - minCapacity) * selectedCapacityAdjustment
  );
}

function InstanceListItem({ instance, isSelected, onSelect, fetchInstances }) {
  const { me = {} } = useConfig();
  const [forks, setForks] = useState(
    computeForks(
      instance.mem_capacity,
      instance.cpu_capacity,
      instance.capacity_adjustment
    )
  );
  const labelId = `check-action-${instance.id}`;

  function usedCapacity(item) {
    if (item.enabled) {
      return (
        <Progress
          value={Math.round(100 - item.percent_capacity_remaining)}
          measureLocation={ProgressMeasureLocation.top}
          size={ProgressSize.sm}
          title={t`Used capacity`}
        />
      );
    }
    return <Unavailable>{t`Unavailable`}</Unavailable>;
  }

  const { error: updateInstanceError, request: updateInstance } = useRequest(
    useCallback(
      async values => {
        await InstancesAPI.update(instance.id, values);
      },
      [instance]
    )
  );

  const {
    error: updateError,
    dismissError: dismissUpdateError,
  } = useDismissableError(updateInstanceError);

  const debounceUpdateInstance = useDebounce(updateInstance, 200);

  const handleChangeValue = value => {
    const roundedValue = Math.round(value * 100) / 100;
    setForks(
      computeForks(instance.mem_capacity, instance.cpu_capacity, roundedValue)
    );
    debounceUpdateInstance({ capacity_adjustment: roundedValue });
  };

  return (
    <>
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
              <DataListCell key="name" aria-label={t`instance host name`}>
                <b>{instance.hostname}</b>
              </DataListCell>,
              <DataListCell key="type" aria-label={t`instance type`}>
                <b css="margin-right: 24px">{t`Type`}</b>
                <span id={labelId}>
                  {instance.managed_by_policy ? t`Auto` : t`Manual`}
                </span>
              </DataListCell>,
              <DataListCell
                key="related-field-counts"
                aria-label={t`instance counts`}
                width={3}
              >
                <ListGroup>
                  <b>{t`Running jobs`}</b>
                  <Badge isRead>{instance.jobs_running}</Badge>
                </ListGroup>
                <ListGroup>
                  <b>{t`Total jobs`}</b>
                  <Badge isRead>{instance.jobs_total}</Badge>
                </ListGroup>
              </DataListCell>,
              <DataListCell
                key="capacity-adjustment"
                aria-label={t`capacity adjustment`}
                width={4}
              >
                <SliderHolder data-cy="slider-holder">
                  <div data-cy="cpu-capacity">{t`CPU ${instance.cpu_capacity}`}</div>
                  <SliderForks data-cy="slider-forks">
                    <div data-cy="number-forks">
                      <Plural value={forks} one="# fork" other="# forks" />
                    </div>
                    <Slider
                      areCustomStepsContinuous
                      max={1}
                      min={0}
                      step={0.1}
                      value={instance.capacity_adjustment}
                      onChange={handleChangeValue}
                      isDisabled={!me?.is_superuser || !instance.enabled}
                      data-cy="slider"
                    />
                  </SliderForks>

                  <div data-cy="mem-capacity">{t`RAM ${instance.mem_capacity}`}</div>
                </SliderHolder>
              </DataListCell>,

              <DataListCell
                key="capacity"
                aria-label={t`instance group used capacity`}
              >
                {usedCapacity(instance)}
              </DataListCell>,
            ]}
          />
          <DataListAction
            aria-label={t`actions`}
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
      {updateError && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen
          onClose={dismissUpdateError}
        >
          {t`Failed to update capacity adjustment.`}
          <ErrorDetail error={updateError} />
        </AlertModal>
      )}
    </>
  );
}

InstanceListItem.prototype = {
  instance: Instance.isRequired,
  isSelected: bool.isRequired,
  onSelect: func.isRequired,
};

export default InstanceListItem;
