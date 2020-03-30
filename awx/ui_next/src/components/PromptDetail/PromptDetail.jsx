import React from 'react';
import { shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Chip, ChipGroup } from '@patternfly/react-core';
import { VariablesDetail } from '@components/CodeMirrorInput';
import { DetailList, Detail } from '@components/DetailList';
import styled from 'styled-components';

const PromptHeader = styled.h2`
  font-weight: bold;
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
      </DetailList>

      {hasPromptData(launchConfig) && (
        <>
          <br />
          <PromptHeader>{i18n._(t`Prompted Values`)}</PromptHeader>
          <br />
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
