import React, { useEffect, useRef, useState } from 'react';
import { Link, useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Button,
  Chip,
  ChipGroup,
  List,
  ListItem,
} from '@patternfly/react-core';
import AlertModal from '@components/AlertModal';
import { CardBody, CardActionsRow } from '@components/Card';
import { VariablesDetail } from '@components/CodeMirrorInput';
import CredentialChip from '@components/CredentialChip';
import DeleteButton from '@components/DeleteButton';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import ErrorDetail from '@components/ErrorDetail';
import { InventorySourcesAPI } from '@api';

function InventorySourceDetail({ inventorySource, i18n }) {
  const {
    created,
    custom_virtualenv,
    description,
    group_by,
    id,
    instance_filters,
    modified,
    name,
    overwrite,
    overwrite_vars,
    source,
    source_path,
    source_regions,
    source_vars,
    update_cache_timeout,
    update_on_launch,
    update_on_project_update,
    verbosity,
    summary_fields: {
      created_by,
      credentials,
      inventory,
      modified_by,
      organization,
      source_project,
      source_script,
      user_capabilities,
    },
  } = inventorySource;
  const [deletionError, setDeletionError] = useState(false);
  const history = useHistory();
  const isMounted = useRef(null);

  useEffect(() => {
    isMounted.current = true;
    return () => {
      isMounted.current = false;
    };
  }, []);

  const handleDelete = async () => {
    try {
      await Promise.all([
        InventorySourcesAPI.destroyHosts(id),
        InventorySourcesAPI.destroyGroups(id),
        InventorySourcesAPI.destroy(id),
      ]);
      history.push(`/inventories/inventory/${inventory.id}/sources`);
    } catch (error) {
      if (isMounted.current) {
        setDeletionError(error);
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
        {overwrite && <ListItem>{i18n._(t`Overwrite`)}</ListItem>}
        {overwrite_vars && (
          <ListItem>{i18n._(t`Overwrite variables`)}</ListItem>
        )}
        {update_on_launch && <ListItem>{i18n._(t`Update on launch`)}</ListItem>}
        {update_on_project_update && (
          <ListItem>{i18n._(t`Update on project update`)}</ListItem>
        )}
      </List>
    );
  }

  return (
    <CardBody>
      <DetailList>
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail label={i18n._(t`Source`)} value={source} />
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
        <Detail label={i18n._(t`Inventory file`)} value={source_path} />
        <Detail
          label={i18n._(t`Custom inventory script`)}
          value={source_script?.name}
        />
        <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[verbosity]} />
        <Detail
          label={i18n._(t`Cache timeout`)}
          value={`${update_cache_timeout} ${i18n._(t`seconds`)}`}
        />
        {credentials?.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credential`)}
            value={credentials.map(cred => (
              <CredentialChip key={cred?.id} credential={cred} isReadOnly />
            ))}
          />
        )}
        {source_regions && (
          <Detail
            fullWidth
            label={i18n._(t`Regions`)}
            value={
              <ChipGroup numChips={5}>
                {source_regions.split(',').map(region => (
                  <Chip key={region} isReadOnly>
                    {region}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {instance_filters && (
          <Detail
            fullWidth
            label={i18n._(t`Instance filters`)}
            value={
              <ChipGroup numChips={5}>
                {instance_filters.split(',').map(filter => (
                  <Chip key={filter} isReadOnly>
                    {filter}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
        {group_by && (
          <Detail
            fullWidth
            label={i18n._(t`Only group by`)}
            value={
              <ChipGroup numChips={5}>
                {group_by.split(',').map(group => (
                  <Chip key={group} isReadOnly>
                    {group}
                  </Chip>
                ))}
              </ChipGroup>
            }
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
            to={`/inventories/inventory/${inventory.id}/source/${id}/edit`}
          >
            {i18n._(t`Edit`)}
          </Button>
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
