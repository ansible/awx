import React, { useCallback, useEffect, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
  Tooltip,
} from '@patternfly/react-core';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig } from 'contexts/Config';
import AlertModal from 'components/AlertModal';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import CredentialChip from 'components/CredentialChip';
import DeleteButton from 'components/DeleteButton';
import ErrorDetail from 'components/ErrorDetail';
import ExecutionEnvironmentDetail from 'components/ExecutionEnvironmentDetail';
import JobCancelButton from 'components/JobCancelButton';
import StatusLabel from 'components/StatusLabel';
import { CardBody, CardActionsRow } from 'components/Card';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import { VariablesDetail } from 'components/CodeEditor';
import useRequest from 'hooks/useRequest';
import { InventorySourcesAPI } from 'api';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import useIsMounted from 'hooks/useIsMounted';
import { formatDateString } from 'util/dates';
import Popover from 'components/Popover';
import { VERBOSITY } from 'components/VerbositySelectField';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';
import useWsInventorySourcesDetails from '../InventorySources/useWsInventorySourcesDetails';
import getHelpText from '../shared/Inventory.helptext';

function InventorySourceDetail({ inventorySource }) {
  const helpText = getHelpText();
  const {
    created,
    custom_virtualenv,
    description,
    id,
    modified,
    name,
    overwrite,
    overwrite_vars,
    source,
    source_path,
    source_vars,
    update_cache_timeout,
    update_on_launch,
    verbosity,
    enabled_var,
    enabled_value,
    host_filter,
    summary_fields,
  } = useWsInventorySourcesDetails(inventorySource);

  const {
    created_by,
    credentials,
    inventory,
    modified_by,
    organization,
    source_project,
    user_capabilities,
    execution_environment,
  } = summary_fields;

  const [deletionError, setDeletionError] = useState(false);
  const config = useConfig();
  const history = useHistory();
  const isMounted = useIsMounted();

  const {
    result: sourceChoices,
    error,
    isLoading,
    request: fetchSourceChoices,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventorySourcesAPI.readOptions();
      return Object.assign(
        ...data.actions.GET.source.choices.map(([key, val]) => ({ [key]: val }))
      );
    }, []),
    {}
  );

  const docsBaseUrl = getDocsBaseUrl(config);
  useEffect(() => {
    fetchSourceChoices();
  }, [fetchSourceChoices]);

  const handleDelete = async () => {
    try {
      await Promise.all([
        InventorySourcesAPI.destroyHosts(id),
        InventorySourcesAPI.destroyGroups(id),
        InventorySourcesAPI.destroy(id),
      ]);
      history.push(`/inventories/inventory/${inventory.id}/sources`);
    } catch (err) {
      if (isMounted.current) {
        setDeletionError(err);
      }
    }
  };

  const deleteDetailsRequests = relatedResourceDeleteRequests.inventorySource(
    inventorySource.id
  );

  let optionsList = '';
  if (overwrite || overwrite_vars || update_on_launch) {
    optionsList = (
      <TextList component={TextListVariants.ul}>
        {overwrite && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Overwrite local groups and hosts from remote inventory source`}
            <Popover content={helpText.subFormOptions.overwrite} />
          </TextListItem>
        )}
        {overwrite_vars && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Overwrite local variables from remote inventory source`}
            <Popover content={helpText.subFormOptions.overwriteVariables} />
          </TextListItem>
        )}
        {update_on_launch && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Update on launch`}
            <Popover
              content={helpText.subFormOptions.updateOnLaunch({
                value: source_project,
              })}
            />
          </TextListItem>
        )}
      </TextList>
    );
  }

  if (isLoading) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  const generateLastJobTooltip = (job) => (
    <>
      <div>{t`MOST RECENT SYNC`}</div>
      <div>
        {t`JOB ID:`} {job.id}
      </div>
      <div>
        {t`STATUS:`} {job.status.toUpperCase()}
      </div>
      {job.finished && (
        <div>
          {t`FINISHED:`} {formatDateString(job.finished)}
        </div>
      )}
    </>
  );

  let job = null;

  if (summary_fields?.current_job) {
    job = summary_fields.current_job;
  } else if (summary_fields?.last_job) {
    job = summary_fields.last_job;
  }

  return (
    <CardBody>
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} />
        <Detail
          label={t`Last Job Status`}
          value={
            job && (
              <Tooltip
                position="top"
                content={generateLastJobTooltip(job)}
                key={job.id}
              >
                <Link to={`/jobs/inventory/${job.id}`}>
                  <StatusLabel status={job.status} />
                </Link>
              </Tooltip>
            )
          }
        />
        <Detail label={t`Description`} value={description} />
        <Detail label={t`Source`} value={sourceChoices[source]} />
        {organization && (
          <Detail
            label={t`Organization`}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
        )}
        <ExecutionEnvironmentDetail
          virtualEnvironment={custom_virtualenv}
          executionEnvironment={execution_environment}
        />
        {source_project && (
          <Detail
            label={t`Project`}
            value={
              <Link to={`/projects/${source_project.id}/details`}>
                {source_project.name}
              </Link>
            }
          />
        )}
        {source === 'scm' ? (
          <Detail
            label={t`Inventory file`}
            helpText={helpText.sourcePath}
            value={source_path === '' ? t`/ (project root)` : source_path}
          />
        ) : null}
        <Detail
          label={t`Verbosity`}
          helpText={helpText.subFormVerbosityFields}
          value={VERBOSITY()[verbosity]}
        />
        <Detail
          label={t`Cache timeout`}
          value={`${update_cache_timeout} ${t`seconds`}`}
          helpText={helpText.subFormOptions.cachedTimeOut}
        />
        <Detail
          label={t`Host Filter`}
          helpText={helpText.hostFilter}
          value={host_filter}
        />
        <Detail
          label={t`Enabled Variable`}
          helpText={helpText.enabledVariableField}
          value={enabled_var}
        />
        <Detail
          label={t`Enabled Value`}
          helpText={helpText.enabledValue}
          value={enabled_value}
        />
        <Detail
          fullWidth
          label={t`Credential`}
          value={credentials?.map((cred) => (
            <CredentialChip key={cred?.id} credential={cred} isReadOnly />
          ))}
          isEmpty={credentials?.length === 0}
        />
        {optionsList && (
          <Detail fullWidth label={t`Enabled Options`} value={optionsList} />
        )}
        {source_vars && (
          <VariablesDetail
            label={t`Source variables`}
            rows={4}
            value={source_vars}
            helpText={helpText.sourceVars(docsBaseUrl, source)}
            name="source_vars"
            dataCy="inventory-source-detail-variables"
          />
        )}
        <UserDateDetail date={created} label={t`Created`} user={created_by} />
        <UserDateDetail
          date={modified}
          label={t`Last modified`}
          user={modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {user_capabilities?.edit && (
          <Button
            ouiaId="inventory-source-detail-edit-button"
            component={Link}
            aria-label={t`edit`}
            to={`/inventories/inventory/${inventory.id}/sources/${id}/edit`}
          >
            {t`Edit`}
          </Button>
        )}
        {user_capabilities?.start &&
          (['new', 'running', 'pending', 'waiting'].includes(job?.status) ? (
            <JobCancelButton
              job={{ id: job.id, type: 'inventory_update' }}
              errorTitle={t`Inventory Source Sync Error`}
              title={t`Cancel Inventory Source Sync`}
              errorMessage={t`Failed to cancel Inventory Source Sync`}
              buttonText={t`Cancel Sync`}
            />
          ) : (
            <InventorySourceSyncButton source={inventorySource} icon={false} />
          ))}
        {user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={t`Delete inventory source`}
            onConfirm={handleDelete}
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This inventory source is currently being used by other resources that rely on it. Are you sure you want to delete it?`}
            isDisabled={job?.status === 'running'}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen={deletionError}
          onClose={() => setDeletionError(false)}
        >
          {t`Failed to delete inventory source ${name}.`}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default InventorySourceDetail;
