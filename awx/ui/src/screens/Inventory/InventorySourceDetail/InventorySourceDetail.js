import React, { useCallback, useEffect, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Button,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
} from '@patternfly/react-core';
import AlertModal from 'components/AlertModal';
import { CardBody, CardActionsRow } from 'components/Card';
import { VariablesDetail } from 'components/CodeEditor';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import CredentialChip from 'components/CredentialChip';
import DeleteButton from 'components/DeleteButton';
import ExecutionEnvironmentDetail from 'components/ExecutionEnvironmentDetail';
import { DetailList, Detail, UserDateDetail } from 'components/DetailList';
import ErrorDetail from 'components/ErrorDetail';
import useRequest from 'hooks/useRequest';
import { InventorySourcesAPI } from 'api';
import { relatedResourceDeleteRequests } from 'util/getRelatedResourceDeleteDetails';
import useIsMounted from 'hooks/useIsMounted';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';

function InventorySourceDetail({ inventorySource }) {
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
    update_on_project_update,
    verbosity,
    enabled_var,
    enabled_value,
    host_filter,
    summary_fields: {
      created_by,
      credentials,
      inventory,
      modified_by,
      organization,
      source_project,
      user_capabilities,
      execution_environment,
    },
  } = inventorySource;
  const [deletionError, setDeletionError] = useState(false);
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

  const VERBOSITY = {
    0: t`0 (Warning)`,
    1: t`1 (Info)`,
    2: t`2 (Debug)`,
  };

  let optionsList = '';
  if (
    overwrite ||
    overwrite_vars ||
    update_on_launch ||
    update_on_project_update
  ) {
    optionsList = (
      <TextList component={TextListVariants.ul}>
        {overwrite && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Overwrite local groups and hosts from remote inventory source`}
          </TextListItem>
        )}
        {overwrite_vars && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Overwrite local variables from remote inventory source`}
          </TextListItem>
        )}
        {update_on_launch && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Update on launch`}
          </TextListItem>
        )}
        {update_on_project_update && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Update on project update`}
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

  return (
    <CardBody>
      <DetailList>
        <Detail label={t`Name`} value={name} />
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
            value={source_path === '' ? t`/ (project root)` : source_path}
          />
        ) : null}
        <Detail label={t`Verbosity`} value={VERBOSITY[verbosity]} />
        <Detail
          label={t`Cache timeout`}
          value={`${update_cache_timeout} ${t`seconds`}`}
        />
        <Detail label={t`Host Filter`} value={host_filter} />
        <Detail label={t`Enabled Variable`} value={enabled_var} />
        <Detail label={t`Enabled Value`} value={enabled_value} />
        {credentials?.length > 0 && (
          <Detail
            fullWidth
            label={t`Credential`}
            value={credentials.map((cred) => (
              <CredentialChip key={cred?.id} credential={cred} isReadOnly />
            ))}
          />
        )}
        {optionsList && (
          <Detail fullWidth label={t`Enabled Options`} value={optionsList} />
        )}
        {source_vars && (
          <VariablesDetail
            label={t`Source variables`}
            rows={4}
            value={source_vars}
            name="source_vars"
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
        {user_capabilities?.start && (
          <InventorySourceSyncButton source={inventorySource} icon={false} />
        )}
        {user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={t`Delete inventory source`}
            onConfirm={handleDelete}
            deleteDetailsRequests={deleteDetailsRequests}
            deleteMessage={t`This inventory source is currently being used by other resources that rely on it. Are you sure you want to delete it?`}
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
