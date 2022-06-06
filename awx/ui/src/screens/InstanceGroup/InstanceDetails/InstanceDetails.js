import React, { useCallback, useEffect, useState } from 'react';

import { useParams, useHistory } from 'react-router-dom';
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
import { CaretLeftIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { useConfig } from 'contexts/Config';
import { InstancesAPI, InstanceGroupsAPI } from 'api';
import useDebounce from 'hooks/useDebounce';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import DisassociateButton from 'components/DisassociateButton';
import InstanceToggle from 'components/InstanceToggle';
import { CardBody, CardActionsRow } from 'components/Card';
import { formatDateString } from 'util/dates';
import RoutedTabs from 'components/RoutedTabs';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { Detail, DetailList } from 'components/DetailList';
import StatusLabel from 'components/StatusLabel';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';

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

function InstanceDetails({ setBreadcrumb, instanceGroup }) {
  const { me = {} } = useConfig();
  const { id, instanceId } = useParams();
  const history = useHistory();

  const [healthCheck, setHealthCheck] = useState({});
  const [forks, setForks] = useState();

  const {
    isLoading,
    error: contentError,
    request: fetchDetails,
    result: { instance },
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await InstanceGroupsAPI.readInstances(instanceGroup.id);
      let instanceDetails;
      let healthCheckDetails;
      const isAssociated = results.some(
        ({ id: instId }) => instId === parseInt(instanceId, 10)
      );

      if (isAssociated) {
        const [{ data: details }, { data: healthCheckData }] =
          await Promise.all([
            InstancesAPI.readDetail(instanceId),
            InstancesAPI.readHealthCheckDetail(instanceId),
          ]);

        instanceDetails = details;
        healthCheckDetails = healthCheckData;
      } else {
        throw new Error(
          `This instance is not associated with this instance group`
        );
      }

      setBreadcrumb(instanceGroup, instanceDetails);
      setHealthCheck(healthCheckDetails);
      setForks(
        computeForks(
          instanceDetails.mem_capacity,
          instanceDetails.cpu_capacity,
          instanceDetails.capacity_adjustment
        )
      );
      return { instance: instanceDetails };
    }, [instanceId, setBreadcrumb, instanceGroup]),
    { instance: {}, isLoading: true }
  );
  useEffect(() => {
    fetchDetails();
  }, [fetchDetails]);

  const {
    error: healthCheckError,
    isLoading: isRunningHealthCheck,
    request: fetchHealthCheck,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InstancesAPI.healthCheck(instanceId);
      setHealthCheck(data);
    }, [instanceId])
  );

  const {
    deleteItems: disassociateInstance,
    deletionError: disassociateError,
  } = useDeleteItems(
    useCallback(async () => {
      await InstanceGroupsAPI.disassociateInstance(
        instanceGroup.id,
        instance.id
      );
      history.push(`/instance_groups/${instanceGroup.id}/instances`);
    }, [instanceGroup.id, instance.id, history])
  );

  const { error: updateInstanceError, request: updateInstance } = useRequest(
    useCallback(
      async (values) => {
        await InstancesAPI.update(instance.id, values);
      },
      [instance]
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
    disassociateError || updateInstanceError || healthCheckError
  );

  const tabsArray = [
    {
      name: (
        <>
          <CaretLeftIcon />
          {t`Back to Instances`}
        </>
      ),
      link: `/instance_groups/${id}/instances`,
      id: 99,
    },
    {
      name: t`Details`,
      link: `/instance_groups/${id}/instances/${instanceId}/details`,
      id: 0,
    },
  ];
  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }

  return (
    <>
      <RoutedTabs tabsArray={tabsArray} />
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
          <Detail label={t`Node Type`} value={instance.node_type} />
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
                  value={Math.round(100 - instance.percent_capacity_remaining)}
                  measureLocation={ProgressMeasureLocation.top}
                  size={ProgressSize.sm}
                  aria-label={t`Used capacity`}
                />
              ) : (
                <Unavailable>{t`Unavailable`}</Unavailable>
              )
            }
          />
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
        <CardActionsRow>
          <Tooltip content={t`Run a health check on the instance`}>
            <Button
              isDisabled={!me.is_superuser || isRunningHealthCheck}
              variant="primary"
              ouiaId="health-check-button"
              onClick={fetchHealthCheck}
              isLoading={isRunningHealthCheck}
              spinnerAriaLabel={t`Running health check`}
            >
              {t`Run health check`}
            </Button>
          </Tooltip>
          {me.is_superuser && instance.node_type !== 'control' && (
            <DisassociateButton
              verifyCannotDisassociate={instanceGroup.name === 'controlplane'}
              key="disassociate"
              onDisassociate={disassociateInstance}
              itemsToDisassociate={[instance]}
              isProtectedInstanceGroup={instanceGroup.name === 'controlplane'}
              modalTitle={t`Disassociate instance from instance group?`}
            />
          )}
          <InstanceToggle
            css="display: inline-flex;"
            fetchInstances={fetchDetails}
            instance={instance}
          />
        </CardActionsRow>

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
    </>
  );
}

export default InstanceDetails;
