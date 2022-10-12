import React, { useCallback, useEffect, useState } from 'react';

import { Link, useHistory, useParams } from 'react-router-dom';
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
  Label,
} from '@patternfly/react-core';
import { DownloadIcon, OutlinedClockIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

import { useConfig } from 'contexts/Config';
import { InstancesAPI } from 'api';
import useDebounce from 'hooks/useDebounce';
import AlertModal from 'components/AlertModal';
import ErrorDetail from 'components/ErrorDetail';
import InstanceToggle from 'components/InstanceToggle';
import { CardBody, CardActionsRow } from 'components/Card';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { formatDateString } from 'util/dates';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { Detail, DetailList } from 'components/DetailList';
import StatusLabel from 'components/StatusLabel';
import useRequest, {
  useDeleteItems,
  useDismissableError,
} from 'hooks/useRequest';
import HealthCheckAlert from 'components/HealthCheckAlert';
import RemoveInstanceButton from '../Shared/RemoveInstanceButton';

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

function InstanceDetail({ setBreadcrumb, isK8s }) {
  const config = useConfig();

  const { id } = useParams();
  const [forks, setForks] = useState();
  const history = useHistory();
  const [healthCheck, setHealthCheck] = useState({});
  const [showHealthCheckAlert, setShowHealthCheckAlert] = useState(false);

  const {
    isLoading,
    error: contentError,
    request: fetchDetails,
    result: { instance, instanceGroups },
  } = useRequest(
    useCallback(async () => {
      const [
        { data: details },
        {
          data: { results },
        },
      ] = await Promise.all([
        InstancesAPI.readDetail(id),
        InstancesAPI.readInstanceGroup(id),
      ]);
      if (details.node_type === 'execution') {
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
      return {
        instance: details,
        instanceGroups: results,
      };
    }, [id]),
    { instance: {}, instanceGroups: [] }
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
      const { status } = await InstancesAPI.healthCheck(id);
      if (status === 200) {
        setShowHealthCheckAlert(true);
      }
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

  const formatHealthCheckTimeStamp = (last) => (
    <>
      {formatDateString(last)}
      {instance.health_check_pending ? (
        <>
          {' '}
          <OutlinedClockIcon />
        </>
      ) : null}
    </>
  );

  const buildLinkURL = (inst) =>
    inst.is_container_group
      ? '/instance_groups/container_group/'
      : '/instance_groups/';

  const { error, dismissError } = useDismissableError(
    updateInstanceError || healthCheckError
  );
  const {
    isLoading: isRemoveLoading,
    deleteItems: removeInstances,
    deletionError: removeError,
    clearDeletionError,
  } = useDeleteItems(
    async () => {
      await InstancesAPI.deprovisionInstance(instance.id);
      history.push('/instances');
    },
    {
      fetchItems: fetchDetails,
    }
  );

  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (isLoading || isRemoveLoading) {
    return <ContentLoading />;
  }
  const isHopNode = instance.node_type === 'hop';
  const isExecutionNode = instance.node_type === 'execution';

  return (
    <>
      {showHealthCheckAlert ? (
        <HealthCheckAlert onSetHealthCheckAlert={setShowHealthCheckAlert} />
      ) : null}
      <CardBody>
        <DetailList gutter="sm">
          <Detail
            label={t`Host Name`}
            value={instance.hostname}
            dataCy="instance-detail-name"
          />
          <Detail
            label={t`Status`}
            dataCy="status"
            value={
              instance.node_state ? (
                <StatusLabel status={instance.node_state} />
              ) : null
            }
          />
          <Detail label={t`Node Type`} value={instance.node_type} />
          {!isHopNode && (
            <>
              <Detail
                label={t`Policy Type`}
                value={instance.managed_by_policy ? t`Auto` : t`Manual`}
              />
              <Detail label={t`Host`} value={instance.ip_address} />
              <Detail label={t`Running Jobs`} value={instance.jobs_running} />
              <Detail label={t`Total Jobs`} value={instance.jobs_total} />
              {instanceGroups && (
                <Detail
                  fullWidth
                  label={t`Instance Groups`}
                  dataCy="instance-groups"
                  helpText={t`The Instance Groups to which this instance belongs.`}
                  value={instanceGroups.map((ig) => (
                    <React.Fragment key={ig.id}>
                      <Label
                        color="blue"
                        isTruncated
                        render={({ className, content, componentRef }) => (
                          <Link
                            to={`${buildLinkURL(ig)}${ig.id}/details`}
                            className={className}
                            innerRef={componentRef}
                          >
                            {content}
                          </Link>
                        )}
                      >
                        {ig.name}
                      </Label>{' '}
                    </React.Fragment>
                  ))}
                  isEmpty={instanceGroups.length === 0}
                />
              )}
              <Detail
                label={t`Last Health Check`}
                dataCy="last-health-check"
                helpText={
                  <>
                    {t`Health checks are asynchronous tasks. See the`}{' '}
                    <a
                      href={`${getDocsBaseUrl(
                        config
                      )}/html/administration/instances.html#health-check`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {t`documentation`}
                    </a>{' '}
                    {t`for more info.`}
                  </>
                }
                value={formatHealthCheckTimeStamp(instance.last_health_check)}
              />
              {instance.related?.install_bundle && (
                <Detail
                  label={t`Install Bundle`}
                  value={
                    <Tooltip content={t`Click to download bundle`}>
                      <Button
                        component="a"
                        isSmall
                        href={`${instance.related?.install_bundle}`}
                        target="_blank"
                        variant="secondary"
                        dataCy="install-bundle-download-button"
                      >
                        <DownloadIcon />
                      </Button>
                    </Tooltip>
                  }
                />
              )}
              <Detail
                label={t`Capacity Adjustment`}
                dataCy="capacity-adjustment"
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
                        isDisabled={
                          !config?.me?.is_superuser || !instance.enabled
                        }
                        data-cy="slider"
                      />
                    </SliderForks>
                    <div data-cy="mem-capacity">{t`RAM ${instance.mem_capacity}`}</div>
                  </SliderHolder>
                }
              />
              <Detail
                label={t`Used Capacity`}
                dataCy="used-capacity"
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
              dataCy="errors"
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
            {config?.me?.is_superuser && isK8s && isExecutionNode && (
              <RemoveInstanceButton
                dataCy="remove-instance-button"
                itemsToRemove={[instance]}
                isK8s={isK8s}
                onRemove={removeInstances}
              />
            )}
            {isExecutionNode && (
              <Tooltip content={t`Run a health check on the instance`}>
                <Button
                  isDisabled={
                    !config?.me?.is_superuser || instance.health_check_pending
                  }
                  variant="primary"
                  ouiaId="health-check-button"
                  onClick={fetchHealthCheck}
                  isLoading={instance.health_check_pending}
                  spinnerAriaLabel={t`Running health check`}
                >
                  {instance.health_check_pending
                    ? t`Running health check`
                    : t`Run health check`}
                </Button>
              </Tooltip>
            )}
            <InstanceToggle
              css="display: inline-flex;"
              fetchInstances={fetchDetails}
              instance={instance}
              dataCy="enable-instance"
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

        {removeError && (
          <AlertModal
            isOpen={removeError}
            variant="error"
            aria-label={t`Removal Error`}
            title={t`Error!`}
            onClose={clearDeletionError}
          >
            {t`Failed to remove one or more instances.`}
            <ErrorDetail error={removeError} />
          </AlertModal>
        )}
      </CardBody>
    </>
  );
}

export default InstanceDetail;
