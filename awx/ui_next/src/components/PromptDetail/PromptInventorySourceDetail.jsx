import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import { Chip, List, ListItem } from '@patternfly/react-core';
import { Detail, DeletedDetail } from '../DetailList';
import { VariablesDetail } from '../CodeMirrorInput';
import CredentialChip from '../CredentialChip';
import ChipGroup from '../ChipGroup';

function PromptInventorySourceDetail({ i18n, resource }) {
  const {
    custom_virtualenv,
    group_by,
    instance_filters,
    overwrite,
    overwrite_vars,
    source,
    source_regions,
    source_vars,
    source_path,
    summary_fields,
    update_cache_timeout,
    update_on_launch,
    update_on_project_update,
    verbosity,
  } = resource;

  const VERBOSITY = {
    0: i18n._(t`0 (Normal)`),
    1: i18n._(t`1 (Verbose)`),
    2: i18n._(t`2 (More Verbose)`),
    3: i18n._(t`3 (Debug)`),
    4: i18n._(t`4 (Connection Debug)`),
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
          <ListItem>{i18n._(t`Overwrite Variables`)}</ListItem>
        )}
        {update_on_launch && <ListItem>{i18n._(t`Update on Launch`)}</ListItem>}
        {update_on_project_update && (
          <ListItem>{i18n._(t`Update on Project Update`)}</ListItem>
        )}
      </List>
    );
  }

  return (
    <>
      {summary_fields?.organization ? (
        <Detail
          label={i18n._(t`Organization`)}
          value={
            <Link
              to={`/organizations/${summary_fields.organization.id}/details`}
            >
              {summary_fields?.organization.name}
            </Link>
          }
        />
      ) : (
        <DeletedDetail label={i18n._(t`Organization`)} />
      )}
      {summary_fields?.inventory && (
        <Detail
          label={i18n._(t`Inventory`)}
          value={
            <Link to={`/inventories/${summary_fields.inventory?.id}/details`}>
              {summary_fields?.inventory?.name}
            </Link>
          }
        />
      )}
      <Detail label={i18n._(t`Source`)} value={source} />
      <Detail
        label={i18n._(t`Ansible Environment`)}
        value={custom_virtualenv}
      />
      {summary_fields?.source_project && (
        <Detail
          label={i18n._(t`Project`)}
          value={
            <Link to={`/projects/${summary_fields.source_project?.id}/details`}>
              {summary_fields.source_project?.name}
            </Link>
          }
        />
      )}
      <Detail label={i18n._(t`Inventory File`)} value={source_path} />
      <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[verbosity]} />
      <Detail
        label={i18n._(t`Cache Timeout`)}
        value={`${update_cache_timeout} ${i18n._(t`Seconds`)}`}
      />
      {summary_fields?.credentials?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Credential`)}
          value={summary_fields.credentials.map(cred => (
            <CredentialChip key={cred?.id} credential={cred} isReadOnly />
          ))}
        />
      )}
      {source_regions && (
        <Detail
          fullWidth
          label={i18n._(t`Regions`)}
          value={
            <ChipGroup
              numChips={5}
              totalChips={source_regions.split(',').length}
            >
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
          label={i18n._(t`Instance Filters`)}
          value={
            <ChipGroup
              numChips={5}
              totalChips={instance_filters.split(',').length}
            >
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
          label={i18n._(t`Only Group By`)}
          value={
            <ChipGroup numChips={5} totalChips={group_by.split(',').length}>
              {group_by.split(',').map(group => (
                <Chip key={group} isReadOnly>
                  {group}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {optionsList && <Detail label={i18n._(t`Options`)} value={optionsList} />}
      {source_vars && (
        <VariablesDetail
          label={i18n._(t`Source Variables`)}
          rows={4}
          value={source_vars}
        />
      )}
    </>
  );
}

export default withI18n()(PromptInventorySourceDetail);
