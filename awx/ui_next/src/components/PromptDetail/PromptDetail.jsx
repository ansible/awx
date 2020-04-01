import React from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t, Trans } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';

import { Chip, ChipGroup } from '@patternfly/react-core';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';

import PromptProjectDetail from './PromptProjectDetail';

const PromptHeader = styled.h2`
  font-weight: bold;
  margin: var(--pf-global--spacer--lg) 0;
`;

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

function formatTimeout(timeout) {
  if (typeof timeout === 'undefined' || timeout === null) {
    return null;
  }
  const minutes = Math.floor(timeout / 60);
  const seconds = timeout - Math.floor(timeout / 60) * 60;
  return (
    <>
      {minutes} <Trans>min</Trans> {seconds} <Trans>sec</Trans>
    </>
  );
}

function PromptDetail({ i18n, resource, launchConfig = {} }) {
  const { defaults = {} } = launchConfig;
  const VERBOSITY = {
    0: i18n._(t`0 (Normal)`),
    1: i18n._(t`1 (Verbose)`),
    2: i18n._(t`2 (More Verbose)`),
    3: i18n._(t`3 (Debug)`),
    4: i18n._(t`4 (Connection Debug)`),
  };

  return (
    <>
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={resource.name} />
        <Detail label={i18n._(t`Description`)} value={resource.description} />
        <Detail
          label={i18n._(t`Type`)}
          value={resource.unified_job_type || resource.type}
        />
        <Detail
          label={i18n._(t`Timeout`)}
          value={formatTimeout(resource?.timeout)}
        />
        {resource?.summary_fields?.organization && (
          <Detail
            label={i18n._(t`Organization`)}
            value={
              <Link
                to={`/organizations/${resource?.summary_fields.organization.id}/details`}
              >
                {resource?.summary_fields?.organization.name}
              </Link>
            }
          />
        )}

        {/* TODO: Add JT, WFJT, Inventory Source Details */}
        {resource?.type === 'project' && (
          <PromptProjectDetail resource={resource} />
        )}

        <UserDateDetail
          label={i18n._(t`Created`)}
          date={resource?.created}
          user={resource?.summary_fields?.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={resource?.modified}
          user={resource?.summary_fields?.modified_by}
        />
      </DetailList>

      {hasPromptData(launchConfig) && (
        <>
          <PromptHeader>{i18n._(t`Prompted Values`)}</PromptHeader>
          <DetailList>
            {launchConfig.ask_job_type_on_launch && (
              <Detail label={i18n._(t`Job Type`)} value={defaults?.job_type} />
            )}
            {launchConfig.ask_credential_on_launch && (
              <Detail
                fullWidth
                label={i18n._(t`Credential`)}
                rows={4}
                value={
                  <ChipGroup numChips={5}>
                    {defaults?.credentials.map(cred => (
                      <Chip key={cred.id} isReadOnly>
                        {cred.name}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {launchConfig.ask_inventory_on_launch && (
              <Detail
                label={i18n._(t`Inventory`)}
                value={defaults?.inventory?.name}
              />
            )}
            {launchConfig.ask_scm_branch_on_launch && (
              <Detail
                label={i18n._(t`SCM Branch`)}
                value={defaults?.scm_branch}
              />
            )}
            {launchConfig.ask_limit_on_launch && (
              <Detail label={i18n._(t`Limit`)} value={defaults?.limit} />
            )}
            {launchConfig.ask_verbosity_on_launch && (
              <Detail
                label={i18n._(t`Verbosity`)}
                value={VERBOSITY[(defaults?.verbosity)]}
              />
            )}
            {launchConfig.ask_tags_on_launch && (
              <Detail
                fullWidth
                label={i18n._(t`Job Tags`)}
                value={
                  <ChipGroup numChips={5}>
                    {defaults?.job_tags.split(',').map(jobTag => (
                      <Chip key={jobTag} isReadOnly>
                        {jobTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {launchConfig.ask_skip_tags_on_launch && (
              <Detail
                fullWidth
                label={i18n._(t`Skip Tags`)}
                value={
                  <ChipGroup numChips={5}>
                    {defaults?.skip_tags.split(',').map(skipTag => (
                      <Chip key={skipTag} isReadOnly>
                        {skipTag}
                      </Chip>
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {launchConfig.ask_diff_mode_on_launch && (
              <Detail
                label={i18n._(t`Diff Mode`)}
                value={
                  defaults?.diff_mode === true ? i18n._(t`On`) : i18n._(t`Off`)
                }
              />
            )}
            {launchConfig.ask_variables_on_launch && (
              <VariablesDetail
                label={i18n._(t`Variables`)}
                rows={4}
                value={defaults?.extra_vars}
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
