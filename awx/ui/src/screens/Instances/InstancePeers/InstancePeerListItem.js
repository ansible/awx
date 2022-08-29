import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import styled from 'styled-components';
import 'styled-components/macro';
import {
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  Slider,
  Tooltip,
} from '@patternfly/react-core';
import { Tr, Td, ExpandableRowContent } from '@patternfly/react-table';
import { formatDateString } from 'util/dates';
import computeForks from 'util/computeForks';
import { ActionsTd, ActionItem } from 'components/PaginatedTable';
import InstanceToggle from 'components/InstanceToggle';
import StatusLabel from 'components/StatusLabel';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import useDebounce from 'hooks/useDebounce';
import { InstancesAPI } from 'api';
import { useConfig } from 'contexts/Config';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import { Detail, DetailList } from 'components/DetailList';

const Unavailable = styled.span`
  color: var(--pf-global--danger-color--200);
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

function InstancePeerListItem({
  peerInstance,
  fetchInstances,
  isSelected,
  onSelect,
  isExpanded,
  onExpand,
  rowIndex,
}) {
  const { me = {} } = useConfig();
  const [forks, setForks] = useState(
    computeForks(
      peerInstance.mem_capacity,
      peerInstance.cpu_capacity,
      peerInstance.capacity_adjustment
    )
  );
  const labelId = `check-action-${peerInstance.id}`;

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
      async (values) => {
        await InstancesAPI.update(peerInstance.id, values);
      },
      [peerInstance]
    )
  );

  const { error: updateError, dismissError: dismissUpdateError } =
    useDismissableError(updateInstanceError);

  const debounceUpdateInstance = useDebounce(updateInstance, 200);

  const handleChangeValue = (value) => {
    const roundedValue = Math.round(value * 100) / 100;
    setForks(
      computeForks(
        peerInstance.mem_capacity,
        peerInstance.cpu_capacity,
        roundedValue
      )
    );
    debounceUpdateInstance({ capacity_adjustment: roundedValue });
  };
  const isHopNode = peerInstance.node_type === 'hop';
  return (
    <>
      <Tr
        id={`peerInstance-row-${peerInstance.id}`}
        ouiaId={`peerInstance-row-${peerInstance.id}`}
      >
        {isHopNode ? (
          <Td />
        ) : (
          <Td
            expand={{
              rowIndex,
              isExpanded,
              onToggle: onExpand,
            }}
          />
        )}
        <Td
          select={{
            rowIndex,
            isSelected,
            onSelect,
            disable: isHopNode,
          }}
          dataLabel={t`Selected`}
        />
        <Td id={labelId} dataLabel={t`Name`}>
          <Link to={`/instances/${peerInstance.id}/details`}>
            <b>{peerInstance.hostname}</b>
          </Link>
        </Td>

        <Td dataLabel={t`Status`}>
          <Tooltip
            content={
              <div>
                {t`Last Health Check`}
                &nbsp;
                {formatDateString(
                  peerInstance.last_health_check ?? peerInstance.last_seen
                )}
              </div>
            }
          >
            <StatusLabel status={peerInstance.node_state} />
          </Tooltip>
        </Td>

        <Td dataLabel={t`Node Type`}>{peerInstance.node_type}</Td>
        {!isHopNode && (
          <>
            <Td dataLabel={t`Capacity Adjustment`}>
              <SliderHolder data-cy="slider-holder">
                <div data-cy="cpu-capacity">{t`CPU ${peerInstance.cpu_capacity}`}</div>
                <SliderForks data-cy="slider-forks">
                  <div data-cy="number-forks">
                    <Plural value={forks} one="# fork" other="# forks" />
                  </div>
                  <Slider
                    areCustomStepsContinuous
                    max={1}
                    min={0}
                    step={0.1}
                    value={peerInstance.capacity_adjustment}
                    onChange={handleChangeValue}
                    isDisabled={!me?.is_superuser || !peerInstance?.enabled}
                    data-cy="slider"
                  />
                </SliderForks>
                <div data-cy="mem-capacity">{t`RAM ${peerInstance.mem_capacity}`}</div>
              </SliderHolder>
            </Td>

            <Td
              dataLabel={t`Instance group used capacity`}
              css="--pf-c-table--cell--MinWidth: 175px;"
            >
              {usedCapacity(peerInstance)}
            </Td>

            <ActionsTd
              dataLabel={t`Actions`}
              css="--pf-c-table--cell--Width: 125px"
            >
              <ActionItem visible>
                <InstanceToggle
                  css="display: inline-flex;"
                  fetchInstances={fetchInstances}
                  instance={peerInstance}
                />
              </ActionItem>
            </ActionsTd>
          </>
        )}
      </Tr>
      {!isHopNode && (
        <Tr
          ouiaId={`peerInstance-row-${peerInstance.id}-expanded`}
          isExpanded={isExpanded}
        >
          <Td colSpan={2} />
          <Td colSpan={7}>
            <ExpandableRowContent>
              <DetailList>
                <Detail
                  data-cy="running-jobs"
                  value={peerInstance.jobs_running}
                  label={t`Running Jobs`}
                />
                <Detail
                  data-cy="total-jobs"
                  value={peerInstance.jobs_total}
                  label={t`Total Jobs`}
                />
                <Detail
                  data-cy="policy-type"
                  label={t`Policy Type`}
                  value={peerInstance.managed_by_policy ? t`Auto` : t`Manual`}
                />
                <Detail
                  data-cy="last-health-check"
                  label={t`Last Health Check`}
                  value={formatDateString(peerInstance.last_health_check)}
                />
              </DetailList>
            </ExpandableRowContent>
          </Td>
        </Tr>
      )}
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

export default InstancePeerListItem;
