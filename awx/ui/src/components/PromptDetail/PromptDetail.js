import 'styled-components/macro';
import React from 'react';
import { shape } from 'prop-types';
import { t, Trans } from '@lingui/macro';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { Chip, Divider, Title } from '@patternfly/react-core';
import { toTitleCase } from 'util/strings';
import CredentialChip from '../CredentialChip';
import ChipGroup from '../ChipGroup';
import { DetailList, Detail, UserDateDetail } from '../DetailList';
import { VariablesDetail } from '../CodeEditor';
import PromptProjectDetail from './PromptProjectDetail';
import PromptInventorySourceDetail from './PromptInventorySourceDetail';
import PromptJobTemplateDetail from './PromptJobTemplateDetail';
import PromptWFJobTemplateDetail from './PromptWFJobTemplateDetail';
import { VERBOSITY } from '../VerbositySelectField';

const PromptTitle = styled(Title)`
  margin-top: var(--pf-global--spacer--xl);
  --pf-c-title--m-md--FontWeight: 700;
  grid-column: 1 / -1;
`;

const PromptDivider = styled(Divider)`
  margin-top: var(--pf-global--spacer--lg);
  margin-bottom: var(--pf-global--spacer--lg);
`;

const PromptDetailList = styled(DetailList)`
  padding: 0px var(--pf-global--spacer--lg);
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

  return link[resource?.type] ? (
    <Link to={link[resource.type]}>{resource.name}</Link>
  ) : (
    resource.name
  );
}

function hasPromptData(launchData) {
  return (
    launchData.survey_enabled ||
    launchData.ask_credential_on_launch ||
    launchData.ask_diff_mode_on_launch ||
    launchData.ask_inventory_on_launch ||
    launchData.ask_job_type_on_launch ||
    launchData.ask_limit_on_launch ||
    launchData.ask_scm_branch_on_launch ||
    launchData.ask_skip_tags_on_launch ||
    launchData.ask_tags_on_launch ||
    launchData.ask_variables_on_launch ||
    launchData.ask_verbosity_on_launch ||
    launchData.ask_execution_environment_on_launch ||
    launchData.ask_labels_on_launch ||
    launchData.ask_forks_on_launch ||
    launchData.ask_job_slice_count_on_launch ||
    launchData.ask_timeout_on_launch ||
    launchData.ask_instance_groups_on_launch
  );
}

function omitOverrides(resource, overrides, defaultConfig) {
  const clonedResource = {
    ...resource,
    summary_fields: { ...resource.summary_fields },
    ...defaultConfig,
  };
  Object.keys(overrides).forEach((keyToOmit) => {
    delete clonedResource[keyToOmit];
    delete clonedResource?.summary_fields[keyToOmit];
  });
  return clonedResource;
}

function PromptDetail({
  resource,
  launchConfig = {},
  overrides = {},
  workflowNode = false,
}) {
  const details = omitOverrides(resource, overrides, launchConfig.defaults);
  details.type = overrides?.nodeType || details.type;
  const hasOverrides = Object.keys(overrides).length > 0;

  return (
    <>
      <DetailList gutter="sm">
        <Detail
          label={t`Name`}
          dataCy="prompt-detail-name"
          value={buildResourceLink(resource)}
        />
        <Detail
          label={t`Description`}
          dataCy="prompt-detail-description"
          value={details.description}
        />
        <Detail
          label={t`Type`}
          dataCy="prompt-detail-type"
          value={toTitleCase(details.unified_job_type || details.type)}
        />
        {workflowNode && (
          <Detail
            label={t`Convergence`}
            dataCy="prompt-detail-convergence"
            value={workflowNode?.all_parents_must_converge ? t`All` : t`Any`}
          />
        )}
        <Detail
          label={t`Timeout`}
          dataCy="prompt-detail-timeout"
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
            label={t`Created`}
            date={details.created}
            user={details?.summary_fields?.created_by}
          />
        )}
        {details?.modified && (
          <UserDateDetail
            label={t`Last Modified`}
            date={details?.modified}
            user={details?.summary_fields?.modified_by}
          />
        )}
        {details?.type === 'system_job_template' && (
          <VariablesDetail
            label={t`Variables`}
            rows={4}
            value={overrides.extra_vars}
            name="extra_vars"
            dataCy="prompt-detail-variables"
          />
        )}
      </DetailList>
      {details?.type !== 'system_job_template' &&
        hasPromptData(launchConfig) &&
        hasOverrides && (
          <>
            <PromptTitle headingLevel="h2">{t`Prompted Values`}</PromptTitle>
            <PromptDivider />
            <PromptDetailList aria-label={t`Prompt Overrides`}>
              {launchConfig.ask_job_type_on_launch && (
                <Detail
                  label={t`Job Type`}
                  value={toTitleCase(overrides.job_type)}
                />
              )}
              {launchConfig.ask_credential_on_launch && (
                <Detail
                  fullWidth
                  label={t`Credentials`}
                  rows={4}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={overrides.credentials.length}
                      ouiaId="prompt-credential-chips"
                    >
                      {overrides.credentials.map((cred) => (
                        <CredentialChip
                          key={cred.id}
                          credential={cred}
                          isReadOnly
                          ouiaId={`credential-${cred.id}-chip`}
                        />
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {launchConfig.ask_inventory_on_launch && (
                <Detail
                  label={t`Inventory`}
                  value={overrides.inventory?.name}
                />
              )}
              {launchConfig.ask_execution_environment_on_launch && (
                <Detail
                  label={t`Execution Environment`}
                  value={overrides.execution_environment?.name}
                />
              )}
              {launchConfig.ask_instance_groups_on_launch && (
                <Detail
                  fullWidth
                  label={t`Instance Groups`}
                  rows={4}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={overrides.instance_groups.length}
                      ouiaId="prompt-instance-groups-chips"
                    >
                      {overrides.instance_groups.map((instance_group) => (
                        <Chip
                          key={instance_group.id}
                          ouiaId={`instance-group-${instance_group.id}-chip`}
                          isReadOnly
                        >
                          {instance_group.name}
                        </Chip>
                      ))}
                    </ChipGroup>
                  }
                />
              )}
              {launchConfig.ask_scm_branch_on_launch && (
                <Detail
                  label={t`Source Control Branch`}
                  value={overrides.scm_branch}
                />
              )}
              {launchConfig.ask_limit_on_launch && (
                <Detail label={t`Limit`} value={overrides.limit} />
              )}
              {Object.prototype.hasOwnProperty.call(overrides, 'verbosity') &&
              launchConfig.ask_verbosity_on_launch ? (
                <Detail
                  label={t`Verbosity`}
                  value={VERBOSITY()[overrides.verbosity]}
                />
              ) : null}
              {launchConfig.ask_tags_on_launch && (
                <Detail
                  fullWidth
                  label={t`Job Tags`}
                  value={
                    <ChipGroup
                      numChips={5}
                      ouiaId="prompt-job-tag-chips"
                      totalChips={
                        !overrides.job_tags || overrides.job_tags === ''
                          ? 0
                          : overrides.job_tags.split(',').length
                      }
                    >
                      {overrides.job_tags.length > 0 &&
                        overrides.job_tags.split(',').map((jobTag) => (
                          <Chip
                            key={jobTag}
                            isReadOnly
                            ouiaId={`job-tag-${jobTag}-chip`}
                          >
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
                  label={t`Skip Tags`}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={
                        !overrides.skip_tags || overrides.skip_tags === ''
                          ? 0
                          : overrides.skip_tags.split(',').length
                      }
                      ouiaId="prompt-skip-tag-chips"
                    >
                      {overrides.skip_tags.length > 0 &&
                        overrides.skip_tags.split(',').map((skipTag) => (
                          <Chip
                            key={skipTag}
                            isReadOnly
                            ouiaId={`skip-tag-${skipTag}-chip`}
                          >
                            {skipTag}
                          </Chip>
                        ))}
                    </ChipGroup>
                  }
                />
              )}
              {launchConfig.ask_labels_on_launch && (
                <Detail
                  fullWidth
                  label={t`Labels`}
                  value={
                    <ChipGroup
                      numChips={5}
                      totalChips={overrides.labels.length}
                      ouiaId="prompt-label-chips"
                    >
                      {overrides.labels.map((label) => (
                        <Chip
                          key={label.id}
                          ouiaId={`label-${label.id}-chip`}
                          isReadOnly
                        >
                          {label.name}
                        </Chip>
                      ))}
                    </ChipGroup>
                  }
                  isEmpty={overrides.labels.length === 0}
                />
              )}
              {launchConfig.ask_forks_on_launch && (
                <Detail label={t`Forks`} value={overrides.forks} />
              )}
              {launchConfig.ask_job_slice_count_on_launch && (
                <Detail
                  label={t`Job Slicing`}
                  value={overrides.job_slice_count}
                />
              )}
              {launchConfig.ask_timeout_on_launch && (
                <Detail label={t`Timeout`} value={overrides.timeout} />
              )}
              {launchConfig.ask_diff_mode_on_launch && (
                <Detail
                  label={t`Show Changes`}
                  value={overrides.diff_mode === true ? t`On` : t`Off`}
                />
              )}
              {(launchConfig.survey_enabled ||
                launchConfig.ask_variables_on_launch) && (
                <VariablesDetail
                  dataCy="prompt-detail-variables"
                  label={t`Variables`}
                  rows={4}
                  value={overrides.extra_vars}
                  name="extra_vars"
                />
              )}
            </PromptDetailList>
          </>
        )}
    </>
  );
}

PromptDetail.defaultProps = {
  launchConfig: { defaults: {} },
};

PromptDetail.propTypes = {
  resource: shape({}).isRequired,
  launchConfig: shape({}),
};

export default PromptDetail;
