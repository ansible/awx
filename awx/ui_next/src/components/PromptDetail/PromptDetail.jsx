import React from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { toTitleCase } from '@util/strings';

import { Chip, ChipGroup, Divider } from '@patternfly/react-core';
import { VariablesDetail } from '@components/CodeMirrorInput';
import CredentialChip from '@components/CredentialChip';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';

import PromptProjectDetail from './PromptProjectDetail';
import PromptInventorySourceDetail from './PromptInventorySourceDetail';
import PromptJobTemplateDetail from './PromptJobTemplateDetail';
import PromptWFJobTemplateDetail from './PromptWFJobTemplateDetail';

const PromptHeader = styled.h2`
  font-weight: bold;
  margin: var(--pf-global--spacer--lg) 0;
`;

function formatTimeout(timeout) {
  if (typeof timeout === 'undefined' || timeout === null) {
    return null;
  }
  const minutes = Math.floor(timeout / 60);
  const seconds = timeout - Math.floor(timeout / 60) * 60;
  return (
    <Trans>
      {minutes} min {seconds} sec
    </Trans>
  );
}

function buildResourceLink(resource) {
  const link = {
    job_template: `/templates/job_template/${resource.id}/details`,
    project: `/projects/${resource.id}/details`,
    inventory_source: `/inventories/inventory/${resource.inventory}/sources/${resource.id}/details`,
    workflow_job_template: `/templates/workflow_job_template/${resource.id}/details`,
  };

  return link[(resource?.type)] ? (
    <Link to={link[resource.type]}>{resource.name}</Link>
  ) : (
    resource.name
  );
}

function hasPromptData(launchData) {
  return (
    launchData.ask_credential_on_launch ||
    launchData.ask_diff_mode_on_launch ||
    launchData.ask_inventory_on_launch ||
    launchData.ask_job_type_on_launch ||
    launchData.ask_limit_on_launch ||
    launchData.ask_scm_branch_on_launch ||
    launchData.ask_skip_tags_on_launch ||
    launchData.ask_tags_on_launch ||
    launchData.ask_variables_on_launch ||
    launchData.ask_verbosity_on_launch
  );
}

function omitOverrides(resource, overrides) {
  const clonedResource = {
    ...resource,
    summary_fields: { ...resource.summary_fields },
  };
  Object.keys(overrides).forEach(keyToOmit => {
    delete clonedResource[keyToOmit];
    delete clonedResource.summary_fields[keyToOmit];
  });
  return clonedResource;
}

// TODO: When prompting is hooked up, update function
// to filter based on prompt overrides
function partitionPromptDetails(resource, launchConfig) {
  const { defaults = {} } = launchConfig;
  const overrides = {};

  if (launchConfig.ask_credential_on_launch) {
    let isEqual;
    const defaultCreds = defaults.credentials;
    const currentCreds = resource?.summary_fields?.credentials;

    if (defaultCreds?.length === currentCreds?.length) {
      isEqual = currentCreds.every(cred => {
        return defaultCreds.some(item => item.id === cred.id);
      });
    } else {
      isEqual = false;
    }

    if (!isEqual) {
      overrides.credentials = resource?.summary_fields?.credentials;
    }
  }
  if (launchConfig.ask_diff_mode_on_launch) {
    if (defaults.diff_mode !== resource.diff_mode) {
      overrides.diff_mode = resource.diff_mode;
    }
  }
  if (launchConfig.ask_inventory_on_launch) {
    if (defaults.inventory.id !== resource.inventory) {
      overrides.inventory = resource?.summary_fields?.inventory;
    }
  }
  if (launchConfig.ask_job_type_on_launch) {
    if (defaults.job_type !== resource.job_type) {
      overrides.job_type = resource.job_type;
    }
  }
  if (launchConfig.ask_limit_on_launch) {
    if (defaults.limit !== resource.limit) {
      overrides.limit = resource.limit;
    }
  }
  if (launchConfig.ask_scm_branch_on_launch) {
    if (defaults.scm_branch !== resource.scm_branch) {
      overrides.scm_branch = resource.scm_branch;
    }
  }
  if (launchConfig.ask_skip_tags_on_launch) {
    if (defaults.skip_tags !== resource.skip_tags) {
      overrides.skip_tags = resource.skip_tags;
    }
  }
  if (launchConfig.ask_tags_on_launch) {
    if (defaults.job_tags !== resource.job_tags) {
      overrides.job_tags = resource.job_tags;
    }
  }
  if (launchConfig.ask_variables_on_launch) {
    if (defaults.extra_vars !== resource.extra_vars) {
      overrides.extra_vars = resource.extra_vars;
    }
  }
  if (launchConfig.ask_verbosity_on_launch) {
    if (defaults.verbosity !== resource.verbosity) {
      overrides.verbosity = resource.verbosity;
    }
  }

  const withoutOverrides = omitOverrides(resource, overrides);

  return [withoutOverrides, overrides];
}

function PromptDetail({ i18n, resource, launchConfig = {} }) {
  const VERBOSITY = {
    0: i18n._(t`0 (Normal)`),
    1: i18n._(t`1 (Verbose)`),
    2: i18n._(t`2 (More Verbose)`),
    3: i18n._(t`3 (Debug)`),
    4: i18n._(t`4 (Connection Debug)`),
  };

  const [details, overrides] = partitionPromptDetails(resource, launchConfig);
  const hasOverrides = Object.keys(overrides).length > 0;

  return (
    <>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={buildResourceLink(resource)} />
        <Detail label={i18n._(t`Description`)} value={details.description} />
        <Detail
          label={i18n._(t`Type`)}
          value={toTitleCase(details.unified_job_type || details.type)}
        />
        <Detail
          label={i18n._(t`Timeout`)}
          value={formatTimeout(details?.timeout)}
        />
        {details?.type === 'project' && (
          <PromptProjectDetail resource={details} />
        )}
        {details?.type === 'inventory_source' && (
          <PromptInventorySourceDetail resource={details} />
        )}
        {details?.type === 'job_template' && (
          <PromptJobTemplateDetail resource={details} />
        )}
        {details?.type === 'workflow_job_template' && (
          <PromptWFJobTemplateDetail resource={details} />
        )}
        {details?.created && (
          <UserDateDetail
            label={i18n._(t`Created`)}
            date={details.created}
            user={details?.summary_fields?.created_by}
          />
        )}
        {details?.modified && (
          <UserDateDetail
            label={i18n._(t`Last Modified`)}
            date={details?.modified}
            user={details?.summary_fields?.modified_by}
          />
        )}
      </DetailList>

      {hasPromptData(launchConfig) && hasOverrides && (
        <>
          <Divider css="margin-top: var(--pf-global--spacer--lg)" />
          <PromptHeader>{i18n._(t`Prompted Values`)}</PromptHeader>
          <DetailList aria-label="Prompt Overrides">
            {overrides?.job_type && (
              <Detail
                label={i18n._(t`Job Type`)}
                value={toTitleCase(overrides.job_type)}
              />
            )}
            {overrides?.credentials && (
              <Detail
                fullWidth
                label={i18n._(t`Credentials`)}
                rows={4}
                value={
                  <ChipGroup numChips={5}>
                    {overrides.credentials.map(cred => (
                      <CredentialChip
                        key={cred.id}
                        credential={cred}
                        isReadOnly
                      />
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {overrides?.inventory && (
              <Detail
                label={i18n._(t`Inventory`)}
                value={overrides.inventory?.name}
              />
            )}
            {overrides?.scm_branch && (
              <Detail
                label={i18n._(t`Source Control Branch`)}
                value={overrides.scm_branch}
              />
            )}
            {overrides?.limit && (
              <Detail label={i18n._(t`Limit`)} value={overrides.limit} />
            )}
            {overrides?.verbosity && (
              <Detail
                label={i18n._(t`Verbosity`)}
                value={VERBOSITY[overrides.verbosity]}
              />
            )}
            {overrides?.job_tags && (
              <Detail
                fullWidth
                label={i18n._(t`Job Tags`)}
                value={
                  <ChipGroup numChips={5}>
                    {overrides.job_tags.split(',').map(jobTag => (
                      <Chip key={jobTag} isReadOnly>
                        {jobTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {overrides?.skip_tags && (
              <Detail
                fullWidth
                label={i18n._(t`Skip Tags`)}
                value={
                  <ChipGroup numChips={5}>
                    {overrides.skip_tags.split(',').map(skipTag => (
                      <Chip key={skipTag} isReadOnly>
                        {skipTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {overrides?.diff_mode && (
              <Detail
                label={i18n._(t`Show Changes`)}
                value={
                  overrides.diff_mode === true ? i18n._(t`On`) : i18n._(t`Off`)
                }
              />
            )}
            {overrides?.extra_vars && (
              <VariablesDetail
                label={i18n._(t`Variables`)}
                rows={4}
                value={overrides.extra_vars}
              />
            )}
          </DetailList>
        </>
      )}
    </>
  );
}

PromptDetail.propTypes = {
  resource: shape({}).isRequired,
  launchConfig: shape({}),
};

export default withI18n()(PromptDetail);
