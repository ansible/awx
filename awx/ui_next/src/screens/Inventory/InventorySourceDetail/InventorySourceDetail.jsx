import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';

import { t } from '@lingui/macro';

import { Button, List, ListItem } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import { VariablesDetail } from '../../../components/CodeEditor';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import DeleteButton from '../../../components/DeleteButton';
import ExecutionEnvironmentDetail from '../../../components/ExecutionEnvironmentDetail';
import InventorySourceSyncButton from '../shared/InventorySourceSyncButton';
import {
  DetailList,
  Detail,
  UserDateDetail,
} from '../../../components/DetailList';
import ErrorDetail from '../../../components/ErrorDetail';
import Popover from '../../../components/Popover';
import useRequest from '../../../util/useRequest';
import { InventorySourcesAPI } from '../../../api';
import { relatedResourceDeleteRequests } from '../../../util/getRelatedResourceDeleteDetails';

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
  const isMounted = useRef(null);

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
    isMounted.current = true;
    fetchSourceChoices();
    return () => {
      isMounted.current = false;
    };
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
    inventorySource.inventory,
    inventorySource
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
      <List>
        {overwrite && (
          <ListItem>
            {t`Overwrite`}
            <Popover
              content={
                <>
                  {t`If checked, any hosts and groups that were
          previously present on the external source but are now removed
          will be removed from the Tower inventory. Hosts and groups
          that were not managed by the inventory source will be promoted
          to the next manually created group or if there is no manually
          created group to promote them into, they will be left in the "all"
          default group for the inventory.`}
                  <br />
                  <br />
                  {t`When not checked, local child
          hosts and groups not found on the external source will remain
          untouched by the inventory update process.`}
                </>
              }
            />
          </ListItem>
        )}
        {overwrite_vars && (
          <ListItem>
            {t`Overwrite variables`}
            <Popover
              content={
                <>
                  {t`If checked, all variables for child groups
                  and hosts will be removed and replaced by those found
                  on the external source.`}
                  <br />
                  <br />
                  {t`When not checked, a merge will be performed,
                  combining local variables with those found on the
                  external source.`}
                </>
              }
            />
          </ListItem>
        )}
        {update_on_launch && (
          <ListItem>
            {t`Update on launch`}
            <Popover
              content={t`Each time a job runs using this inventory,
        refresh the inventory from the selected source before
        executing job tasks.`}
            />
          </ListItem>
        )}
        {update_on_project_update && (
          <ListItem>
            {t`Update on project update`}
            <Popover
              content={t`After every project update where the SCM revision
        changes, refresh the inventory from the selected source
        before executing job tasks. This is intended for static content,
        like the Ansible inventory .ini file format.`}
            />
          </ListItem>
        )}
      </List>
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
            value={credentials.map(cred => (
              <CredentialChip key={cred?.id} credential={cred} isReadOnly />
            ))}
          />
        )}
        {optionsList && (
          <Detail fullWidth label={t`Options`} value={optionsList} />
        )}
        {source_vars && (
          <VariablesDetail
            label={t`Source variables`}
            rows={4}
            value={source_vars}
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
