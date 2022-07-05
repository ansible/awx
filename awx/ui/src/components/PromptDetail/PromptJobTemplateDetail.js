import React from 'react';
import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';
import {
  Chip,
  TextList,
  TextListItem,
  TextListVariants,
  TextListItemVariants,
} from '@patternfly/react-core';
import { toTitleCase } from 'util/strings';
import CredentialChip from '../CredentialChip';
import ChipGroup from '../ChipGroup';
import Sparkline from '../Sparkline';
import { Detail, DeletedDetail } from '../DetailList';
import { VariablesDetail } from '../CodeEditor';
import ExecutionEnvironmentDetail from '../ExecutionEnvironmentDetail';
import { VERBOSITY } from '../VerbositySelectField';

function PromptJobTemplateDetail({ resource }) {
  const {
    allow_simultaneous,
    ask_inventory_on_launch,
    become_enabled,
    diff_mode,
    extra_vars,
    forks,
    host_config_key,
    instance_groups = [],
    job_slice_count,
    job_tags,
    job_type,
    limit,
    playbook,
    related,
    scm_branch,
    skip_tags,
    summary_fields,
    use_fact_cache,
    verbosity,
    webhook_key,
    webhook_service,
    custom_virtualenv,
  } = resource;

  let optionsList = '';
  if (
    become_enabled ||
    host_config_key ||
    allow_simultaneous ||
    use_fact_cache ||
    webhook_service
  ) {
    optionsList = (
      <TextList component={TextListVariants.ul}>
        {become_enabled && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Privilege Escalation`}
          </TextListItem>
        )}
        {host_config_key && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Provisioning Callbacks`}
          </TextListItem>
        )}
        {allow_simultaneous && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Concurrent Jobs`}
          </TextListItem>
        )}
        {use_fact_cache && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Fact Storage`}
          </TextListItem>
        )}
        {webhook_service && (
          <TextListItem component={TextListItemVariants.li}>
            {t`Webhooks`}
          </TextListItem>
        )}
      </TextList>
    );
  }

  const inventoryKind =
    summary_fields?.inventory?.kind === 'smart'
      ? 'smart_inventory'
      : 'inventory';

  const recentJobs = summary_fields?.recent_jobs?.map((job) => ({
    ...job,
    type: 'job',
  }));

  return (
    <>
      <Detail
        label={t`Activity`}
        value={<Sparkline jobs={recentJobs} />}
        isEmpty={summary_fields.recent_jobs?.length === 0}
      />
      <Detail label={t`Job Type`} value={toTitleCase(job_type)} />
      {summary_fields?.organization ? (
        <Detail
          label={t`Organization`}
          value={
            <Link
              to={`/organizations/${summary_fields.organization.id}/details`}
            >
              {summary_fields?.organization.name}
            </Link>
          }
        />
      ) : (
        <DeletedDetail label={t`Organization`} />
      )}
      {summary_fields?.inventory ? (
        <Detail
          label={t`Inventory`}
          value={
            <Link
              to={`/inventories/${inventoryKind}/${summary_fields.inventory?.id}/details`}
            >
              {summary_fields.inventory?.name}
            </Link>
          }
        />
      ) : (
        !ask_inventory_on_launch && <DeletedDetail label={t`Inventory`} />
      )}
      {summary_fields?.project ? (
        <Detail
          label={t`Project`}
          value={
            <Link to={`/projects/${summary_fields.project?.id}/details`}>
              {summary_fields.project?.name}
            </Link>
          }
        />
      ) : (
        <DeletedDetail label={t`Project`} />
      )}
      <ExecutionEnvironmentDetail
        virtualEnvironment={custom_virtualenv}
        executionEnvironment={summary_fields?.execution_environment}
      />
      <Detail label={t`Source Control Branch`} value={scm_branch} />
      <Detail label={t`Playbook`} value={playbook} />
      <Detail label={t`Forks`} value={forks || '0'} />
      <Detail label={t`Limit`} value={limit} />
      <Detail label={t`Verbosity`} value={VERBOSITY()[verbosity]} />
      {typeof diff_mode === 'boolean' && (
        <Detail label={t`Show Changes`} value={diff_mode ? t`On` : t`Off`} />
      )}
      <Detail label={t` Job Slicing`} value={job_slice_count} />
      <Detail label={t`Host Config Key`} value={host_config_key} />
      {related?.callback && (
        <Detail
          label={t`Provisioning Callback URL`}
          value={`${window.location.origin}${related.callback}`}
        />
      )}
      <Detail label={t`Webhook Service`} value={toTitleCase(webhook_service)} />
      {related?.webhook_receiver && (
        <Detail
          label={t`Webhook URL`}
          value={`${window.location.origin}${related.webhook_receiver}`}
        />
      )}
      <Detail label={t`Webhook Key`} value={webhook_key} />
      {summary_fields?.webhook_credential && (
        <Detail
          fullWidth
          label={t`Webhook Credential`}
          value={
            <CredentialChip
              key={summary_fields.webhook_credential?.id}
              credential={summary_fields.webhook_credential}
              isReadOnly
            />
          }
        />
      )}
      {optionsList && <Detail label={t`Enabled Options`} value={optionsList} />}
      {summary_fields?.credentials && (
        <Detail
          fullWidth
          label={t`Credentials`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={summary_fields.credentials.length}
              ouiaId="prompt-jt-credential-chips"
            >
              {summary_fields.credentials.map((cred) => (
                <CredentialChip key={cred.id} credential={cred} isReadOnly />
              ))}
            </ChipGroup>
          }
          isEmpty={summary_fields?.credentials?.length === 0}
        />
      )}
      {summary_fields?.labels?.results && (
        <Detail
          fullWidth
          label={t`Labels`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={summary_fields.labels.results.length}
              ouiaId="prompt-jt-label-chips"
            >
              {summary_fields.labels.results.map((label) => (
                <Chip key={label.id} isReadOnly>
                  {label.name}
                </Chip>
              ))}
            </ChipGroup>
          }
          isEmpty={summary_fields?.labels?.results?.length === 0}
        />
      )}
      <Detail
        fullWidth
        label={t`Instance Groups`}
        value={
          <ChipGroup
            numChips={5}
            totalChips={instance_groups?.length}
            ouiaId="prompt-jt-instance-group-chips"
          >
            {instance_groups?.map((ig) => (
              <Chip key={ig.id} isReadOnly>
                {ig.name}
              </Chip>
            ))}
          </ChipGroup>
        }
        isEmpty={instance_groups?.length === 0}
      />
      {job_tags && (
        <Detail
          fullWidth
          label={t`Job Tags`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={job_tags.split(',').length}
              ouiaId="prompt-jt-job-tag-chips"
            >
              {job_tags.split(',').map((jobTag) => (
                <Chip key={jobTag} isReadOnly>
                  {jobTag}
                </Chip>
              ))}
            </ChipGroup>
          }
          isEmpty={job_tags?.length === 0}
        />
      )}
      {skip_tags && (
        <Detail
          fullWidth
          label={t`Skip Tags`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={skip_tags.split(',').length}
              ouiaId="prompt-jt-skip-tag-chips"
            >
              {skip_tags.split(',').map((skipTag) => (
                <Chip key={skipTag} isReadOnly>
                  {skipTag}
                </Chip>
              ))}
            </ChipGroup>
          }
          isEmpty={skip_tags?.length === 0}
        />
      )}
      {extra_vars && (
        <VariablesDetail
          label={t`Variables`}
          rows={4}
          value={extra_vars}
          name="extra_vars"
          dataCy="prompt-jt-detail-extra-vars"
        />
      )}
    </>
  );
}

export default PromptJobTemplateDetail;
