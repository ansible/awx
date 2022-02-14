import React, { useCallback, useEffect, useState } from 'react';

import { useParams } from 'react-router-dom';
import { t, Plural } from '@lingui/macro';
import {
  Button,
  Progress,
  ProgressMeasureLocation,
  ProgressSize,
  CodeBlock,
  CodeBlockCode,
  Tooltip,
  Slider,
} from '@patternfly/react-core';
import styled from 'styled-components';

import { useConfig } from 'contexts/Config';
import { InstancesAPI } from 'api';
import useDebounce from 'hooks/useDebounce';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import InstanceToggle from 'components/InstanceToggle';
import { CardBody, CardActionsRow } from 'components/Card';
import { formatDateString } from 'util/dates';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { Detail, DetailList } from 'components/DetailList';
import StatusLabel from 'components/StatusLabel';
import useRequest, { useDismissableError } from 'hooks/useRequest';

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

function computeForks(memCapacity, cpuCapacity, selectedCapacityAdjustment) {
  const minCapacity = Math.min(memCapacity, cpuCapacity);
  const maxCapacity = Math.max(memCapacity, cpuCapacity);

  return Math.floor(
    minCapacity + (maxCapacity - minCapacity) * selectedCapacityAdjustment
  );
}

function InstanceDetail({ setBreadcrumb }) {
  const { me = {} } = useConfig();
  const { id } = useParams();
  const [forks, setForks] = useState();

  const [healthCheck, setHealthCheck] = useState({});

  const {
    isLoading,
    error: contentError,
    request: fetchDetails,
    result: instance,
  } = useRequest(
    useCallback(async () => {
      const { data: details } = await InstancesAPI.readDetail(id);

      if (details.node_type !== 'hop') {
        const { data: healthCheckData } =
          await InstancesAPI.readHealthCheckDetail(id);
        setHealthCheck(healthCheckData);
      }

      setForks(
        computeForks(
          details.mem_capacity,
          details.cpu_capacity,
          details.capacity_adjustment
        )
      );
      return details;
    }, [id]),
    {}
  );
  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  useEffect(() => {
    if (instance) {
      setBreadcrumb(instance);
    }
  }, [instance, setBreadcrumb]);

  const { error: healthCheckError, request: fetchHealthCheck } = useRequest(
    useCallback(async () => {
      const { data } = await InstancesAPI.healthCheck(id);
      setHealthCheck(data);
    }, [id])
  );

  const { error: updateInstanceError, request: updateInstance } = useRequest(
    useCallback(
      async (values) => {
        await InstancesAPI.update(id, values);
      },
      [id]
    )
  );

  const debounceUpdateInstance = useDebounce(updateInstance, 200);

  const handleChangeValue = (value) => {
    const roundedValue = Math.round(value * 100) / 100;
    setForks(
      computeForks(instance.mem_capacity, instance.cpu_capacity, roundedValue)
    );
    debounceUpdateInstance({ capacity_adjustment: roundedValue });
  };

  const { error, dismissError } = useDismissableError(
    updateInstanceError || healthCheckError
  );
  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }
  const isHopNode = instance.node_type === 'hop';
  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail
          label={t`Host Name`}
          value={instance.hostname}
          dataCy="instance-detail-name"
        />
        <Detail
          label={t`Status`}
          value={
            <StatusLabel status={healthCheck?.errors ? 'error' : 'healthy'} />
          }
        />
        <Detail label={t`Node Type`} value={instance.node_type} />
        {!isHopNode && (
          <>
            <Detail
              label={t`Policy Type`}
              value={instance.managed_by_policy ? t`Auto` : t`Manual`}
            />
            <Detail label={t`Running Jobs`} value={instance.jobs_running} />
            <Detail label={t`Total Jobs`} value={instance.jobs_total} />
            <Detail
              label={t`Last Health Check`}
              value={formatDateString(healthCheck?.last_health_check)}
            />
            <Detail
              label={t`Capacity Adjustment`}
              value={
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
              }
            />
            <Detail
              label={t`Used Capacity`}
              value={
                instance.enabled ? (
                  <Progress
                    title={t`Used capacity`}
                    value={Math.round(
                      100 - instance.percent_capacity_remaining
                    )}
                    measureLocation={ProgressMeasureLocation.top}
                    size={ProgressSize.sm}
                    aria-label={t`Used capacity`}
                  />
                ) : (
                  <Unavailable>{t`Unavailable`}</Unavailable>
                )
              }
            />
          </>
        )}
        {healthCheck?.errors && (
          <Detail
            fullWidth
            label={t`Errors`}
            value={
              <CodeBlock>
                <CodeBlockCode>{healthCheck?.errors}</CodeBlockCode>
              </CodeBlock>
            }
          />
        )}
      </DetailList>
      {!isHopNode && (
        <CardActionsRow>
          <Tooltip content={t`Run a health check on the instance`}>
            <Button
              isDisabled={!me.is_superuser}
              variant="primary"
              ouiaId="health-check-button"
              onClick={fetchHealthCheck}
            >
              {t`Health Check`}
            </Button>
          </Tooltip>
          <InstanceToggle
            css="display: inline-flex;"
            fetchInstances={fetchDetails}
            instance={instance}
          />
        </CardActionsRow>
      )}

      {error && (
        <AlertModal
          isOpen={error}
          onClose={dismissError}
          title={t`Error!`}
          variant="error"
        >
          {updateInstanceError
            ? t`Failed to update capacity adjustment.`
            : t`Failed to disassociate one or more instances.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

export default InstanceDetail;
