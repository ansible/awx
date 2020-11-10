import React, { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Button, List, ListItem } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import { VariablesDetail } from '../../../components/CodeMirrorInput';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import DeleteButton from '../../../components/DeleteButton';
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

function InventorySourceDetail({ inventorySource, i18n }) {
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

  const VERBOSITY = {
    0: i18n._(t`0 (Warning)`),
    1: i18n._(t`1 (Info)`),
    2: i18n._(t`2 (Debug)`),
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
            {i18n._(t`Overwrite`)}
            <Popover
              content={
                <>
                  {i18n._(t`If checked, any hosts and groups that were
          previously present on the external source but are now removed
          will be removed from the Tower inventory. Hosts and groups
          that were not managed by the inventory source will be promoted
          to the next manually created group or if there is no manually
          created group to promote them into, they will be left in the "all"
          default group for the inventory.`)}
                  <br />
                  <br />
                  {i18n._(t`When not checked, local child
          hosts and groups not found on the external source will remain
          untouched by the inventory update process.`)}
                </>
              }
            />
          </ListItem>
        )}
        {overwrite_vars && (
          <ListItem>
            {i18n._(t`Overwrite variables`)}
            <Popover
              content={
                <>
                  {i18n._(t`If checked, all variables for child groups
                  and hosts will be removed and replaced by those found
                  on the external source.`)}
                  <br />
                  <br />
                  {i18n._(t`When not checked, a merge will be performed,
                  combining local variables with those found on the
                  external source.`)}
                </>
              }
            />
          </ListItem>
        )}
        {update_on_launch && (
          <ListItem>
            {i18n._(t`Update on launch`)}
            <Popover
              content={i18n._(t`Each time a job runs using this inventory,
        refresh the inventory from the selected source before
        executing job tasks.`)}
            />
          </ListItem>
        )}
        {update_on_project_update && (
          <ListItem>
            {i18n._(t`Update on project update`)}
            <Popover
              content={i18n._(t`After every project update where the SCM revision
        changes, refresh the inventory from the selected source
        before executing job tasks. This is intended for static content,
        like the Ansible inventory .ini file format.`)}
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
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Source`)} value={sourceChoices[source]} />
        {organization && (
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link to={`/organizations/${organization.id}/details`}>
                {organization.name}
              </Link>
            }
          />
        )}
        <Detail
          label={i18n._(t`Ansible environment`)}
          value={custom_virtualenv}
        />
        {source_project && (
          <Detail
            label={i18n._(t`Project`)}
            value={
              <Link to={`/projects/${source_project.id}/details`}>
                {source_project.name}
              </Link>
            }
          />
        )}
        <Detail
          label={i18n._(t`Inventory file`)}
          value={source_path === '' ? i18n._(t`/ (project root)`) : source_path}
        />
        <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[verbosity]} />
        <Detail
          label={i18n._(t`Cache timeout`)}
          value={`${update_cache_timeout} ${i18n._(t`seconds`)}`}
        />
        <Detail label={i18n._(t`Host Filter`)} value={host_filter} />
        <Detail label={i18n._(t`Enabled Variable`)} value={enabled_var} />
        <Detail label={i18n._(t`Enabled Value`)} value={enabled_value} />
        {credentials?.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credential`)}
            value={credentials.map(cred => (
              <CredentialChip key={cred?.id} credential={cred} isReadOnly />
            ))}
          />
        )}
        {optionsList && (
          <Detail fullWidth label={i18n._(t`Options`)} value={optionsList} />
        )}
        {source_vars && (
          <VariablesDetail
            label={i18n._(t`Source variables`)}
            rows={4}
            value={source_vars}
          />
        )}
        <UserDateDetail
          date={created}
          label={i18n._(t`Created`)}
          user={created_by}
        />
        <UserDateDetail
          date={modified}
          label={i18n._(t`Last modified`)}
          user={modified_by}
        />
      </DetailList>
      <CardActionsRow>
        {user_capabilities?.edit && (
          <Button
            component={Link}
            aria-label={i18n._(t`edit`)}
            to={`/inventories/inventory/${inventory.id}/sources/${id}/edit`}
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {user_capabilities?.start && (
          <InventorySourceSyncButton source={inventorySource} icon={false} />
        )}
        {user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={i18n._(t`Delete inventory source`)}
            onConfirm={handleDelete}
          >
            {i18n._(t`Delete`)}
          </DeleteButton>
        )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={deletionError}
          onClose={() => setDeletionError(false)}
        >
          {i18n._(t`Failed to delete inventory source ${name}.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}
export default withI18n()(InventorySourceDetail);
