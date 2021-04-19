import React from 'react';

import { t } from '@lingui/macro';
import { Link } from 'react-router-dom';

import { Chip, List, ListItem } from '@patternfly/react-core';
import CredentialChip from '../CredentialChip';
import ChipGroup from '../ChipGroup';
import { Detail } from '../DetailList';
import { VariablesDetail } from '../CodeEditor';
import Sparkline from '../Sparkline';
import { toTitleCase } from '../../util/strings';

function PromptWFJobTemplateDetail({ resource }) {
  const {
    allow_simultaneous,
    extra_vars,
    limit,
    related,
    scm_branch,
    summary_fields,
    webhook_key,
    webhook_service,
  } = resource;

  let optionsList = '';
  if (allow_simultaneous || webhook_service) {
    optionsList = (
      <List>
        {allow_simultaneous && <ListItem>{t`Enable Concurrent Jobs`}</ListItem>}
        {webhook_service && <ListItem>{t`Enable Webhooks`}</ListItem>}
      </List>
    );
  }

  const inventoryKind =
    summary_fields?.inventory?.kind === 'smart'
      ? 'smart_inventory'
      : 'inventory';

  const recentJobs = summary_fields?.recent_jobs?.map(job => ({
    ...job,
    type: 'job',
  }));

  return (
    <>
      {summary_fields?.recent_jobs?.length > 0 && (
        <Detail value={<Sparkline jobs={recentJobs} />} label={t`Activity`} />
      )}
      {summary_fields?.organization && (
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
      )}
      {summary_fields?.inventory && (
        <Detail
          label={t`Inventory`}
          value={
            <Link
              to={`/${inventoryKind}/${summary_fields.inventory?.id}/details`}
            >
              {summary_fields.inventory?.name}
            </Link>
          }
        />
      )}
      <Detail label={t`Source Control Branch`} value={scm_branch} />
      <Detail label={t`Limit`} value={limit} />
      <Detail label={t`Webhook Service`} value={toTitleCase(webhook_service)} />
      <Detail label={t`Webhook Key`} value={webhook_key} />
      {related?.webhook_receiver && (
        <Detail
          label={t`Webhook URL`}
          value={`${window.location.origin}${related.webhook_receiver}`}
        />
      )}
      {optionsList && <Detail label={t`Options`} value={optionsList} />}
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
      {summary_fields?.labels?.results?.length > 0 && (
        <Detail
          fullWidth
          label={t`Labels`}
          value={
            <ChipGroup
              numChips={5}
              totalChips={summary_fields.labels.results.length}
            >
              {summary_fields.labels.results.map(label => (
                <Chip key={label.id} isReadOnly>
                  {label.name}
                </Chip>
              ))}
            </ChipGroup>
          }
        />
      )}
      {extra_vars && (
        <VariablesDetail label={t`Variables`} rows={4} value={extra_vars} />
      )}
    </>
  );
}

export default PromptWFJobTemplateDetail;
