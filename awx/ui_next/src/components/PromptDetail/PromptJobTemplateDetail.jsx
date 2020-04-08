import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import { Chip, ChipGroup, List, ListItem } from '@patternfly/react-core';
import { Detail } from '@components/DetailList';
import { VariablesDetail } from '@components/CodeMirrorInput';
import CredentialChip from '@components/CredentialChip';

function PromptJobTemplateDetail({ i18n, resource }) {
  const {
    allow_simultaneous,
    become_enabled,
    diff_mode,
    extra_vars,
    forks,
    host_config_key,
    instance_groups,
    job_slice_count,
    job_tags,
    job_type,
    limit,
    playbook,
    scm_branch,
    skip_tags,
    summary_fields,
    url,
    use_fact_cache,
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
    become_enabled ||
    host_config_key ||
    allow_simultaneous ||
    use_fact_cache
  ) {
    optionsList = (
      <List>
        {become_enabled && (
          <ListItem>{i18n._(t`Enable Privilege Escalation`)}</ListItem>
        )}
        {host_config_key && (
          <ListItem>{i18n._(t`Allow Provisioning Callbacks`)}</ListItem>
        )}
        {allow_simultaneous && (
          <ListItem>{i18n._(t`Enable Concurrent Jobs`)}</ListItem>
        )}
        {use_fact_cache && <ListItem>{i18n._(t`Use Fact Storage`)}</ListItem>}
      </List>
    );
  }

  return (
    <>
      <Detail label={i18n._(t`Job Type`)} value={job_type} />
      {summary_fields?.inventory && (
        <Detail
          label={i18n._(t`Inventory`)}
          value={
            <Link to={`/inventories/${summary_fields.inventory?.id}/details`}>
              {summary_fields.inventory?.name}
            </Link>
          }
        />
      )}
      {summary_fields?.project && (
        <Detail
          label={i18n._(t`Project`)}
          value={
            <Link to={`/projects/${summary_fields.project?.id}/details`}>
              {summary_fields.project?.name}
            </Link>
          }
        />
      )}
      <Detail label={i18n._(t`SCM Branch`)} value={scm_branch} />
      <Detail label={i18n._(t`Playbook`)} value={playbook} />
      <Detail label={i18n._(t`Forks`)} value={forks || '0'} />
      <Detail label={i18n._(t`Limit`)} value={limit} />
      <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[verbosity]} />
      <Detail
        label={i18n._(t`Show Changes`)}
        value={diff_mode ? 'On' : 'Off'}
      />
      <Detail label={i18n._(t` Job Slicing`)} value={job_slice_count} />
      {host_config_key && (
        <React.Fragment>
          <Detail label={i18n._(t`Host Config Key`)} value={host_config_key} />
          <Detail
            label={i18n._(t`Provisioning Callback URL`)}
            value={`${window.location.origin + url}callback/`}
          />
        </React.Fragment>
      )}
      {summary_fields?.credentials?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Credentials`)}
          value={summary_fields.credentials.map(chip => (
            <CredentialChip key={chip.id} credential={chip} isReadOnly />
          ))}
        />
      )}
      {summary_fields?.labels?.results?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Labels`)}
          value={
            <ChipGroup numChips={5}>
              {summary_fields.labels.results.map(label => (
                <Chip key={label.id} isReadOnly>
                  {label.name}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {instance_groups?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Instance Groups`)}
          value={
            <ChipGroup numChips={5}>
              {instance_groups.map(ig => (
                <Chip key={ig.id} isReadOnly>
                  {ig.name}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {job_tags?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Job Tags`)}
          value={
            <ChipGroup numChips={5}>
              {job_tags.split(',').map(jobTag => (
                <Chip key={jobTag} isReadOnly>
                  {jobTag}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {skip_tags?.length > 0 && (
        <Detail
          fullWidth
          label={i18n._(t`Skip Tags`)}
          value={
            <ChipGroup numChips={5}>
              {skip_tags.split(',').map(skipTag => (
                <Chip key={skipTag} isReadOnly>
                  {skipTag}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {optionsList && <Detail label={i18n._(t`Options`)} value={optionsList} />}
      {extra_vars && (
        <VariablesDetail
          label={i18n._(t`Variables`)}
          rows={4}
          value={extra_vars}
        />
      )}
    </>
  );
}

export default withI18n()(PromptJobTemplateDetail);
