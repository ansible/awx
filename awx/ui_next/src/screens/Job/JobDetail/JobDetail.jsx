import React from 'react';
import { shape } from 'prop-types';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip, CredentialChip } from '@components/Chip';
import { VariablesInput } from '@components/CodeMirrorInput';
import { toTitleCase } from '@util/strings';

const ActionButtonWrapper = styled.div`
  display: flex;
  justify-content: flex-end;
`;

const VERBOSITY = {
  0: '0 (Normal)',
  1: '1 (Verbose)',
  2: '2 (More Verbose)',
  3: '3 (Debug)',
  4: '4 (Connection Debug)',
};

function JobDetail({ job, i18n }) {
  const {
    job_template: jobTemplate,
    project,
    inventory,
    instance_group: instanceGroup,
    credentials,
    labels,
  } = job.summary_fields;

  return (
    <CardBody>
      <DetailList>
        {/* TODO: add status icon? */}
        <Detail label={i18n._(t`Status`)} value={toTitleCase(job.status)} />
        <Detail label={i18n._(t`Started`)} value={job.started} />
        <Detail label={i18n._(t`Finished`)} value={job.finished} />
        {jobTemplate && (
          <Detail
            label={i18n._(t`Template`)}
            value={
              <Link to={`/templates/job_template/${jobTemplate.id}`}>
                {jobTemplate.name}
              </Link>
            }
          />
        )}
        <Detail label={i18n._(t`Job Type`)} value={toTitleCase(job.job_type)} />
        {inventory && (
          <Detail
            label={i18n._(t`Inventory`)}
            value={
              <Link to={`/inventory/${inventory.id}`}>{inventory.name}</Link>
            }
          />
        )}
        {/* TODO: show project status icon */}
        {project && (
          <Detail
            label={i18n._(t`Project`)}
            value={<Link to={`/projects/${project.id}`}>{project.name}</Link>}
          />
        )}
        <Detail label={i18n._(t`Revision`)} value={job.scm_revision} />
        <Detail label={i18n._(t`Playbook`)} value={null} />
        <Detail label={i18n._(t`Limit`)} value={job.limit} />
        <Detail label={i18n._(t`Verbosity`)} value={VERBOSITY[job.verbosity]} />
        <Detail label={i18n._(t`Environment`)} value={null} />
        <Detail label={i18n._(t`Execution Node`)} value={job.exucution_node} />
        {instanceGroup && (
          <Detail
            label={i18n._(t`Instance Group`)}
            value={
              <Link to={`/instance_groups/${instanceGroup.id}`}>
                {instanceGroup.name}
              </Link>
            }
          />
        )}
        {typeof job.job_slice_number === 'number' &&
          typeof job.job_slice_count === 'number' && (
            <Detail
              label={i18n._(t`Job Slice`)}
              value={`${job.job_slice_number}/${job.job_slice_count}`}
            />
          )}
        {credentials && credentials.length > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credentials`)}
            value={
              <ChipGroup showOverflowAfter={5}>
                {credentials.map(c => (
                  <CredentialChip key={c.id} credential={c} isReadOnly />
                ))}
              </ChipGroup>
            }
          />
        )}
        {labels && labels.count > 0 && (
          <Detail
            fullWidth
            label={i18n._(t`Credentials`)}
            value={
              <ChipGroup showOverflowAfter={5}>
                {labels.results.map(l => (
                  <Chip key={l.id} isReadOnly>
                    {l.name}
                  </Chip>
                ))}
              </ChipGroup>
            }
          />
        )}
      </DetailList>
      {job.extra_vars && (
        <VariablesInput
          css="margin: 20px 0"
          id="job-variables"
          readOnly
          value={job.extra_vars}
          rows={4}
          label={i18n._(t`Variables`)}
        />
      )}
      <VariablesInput
        css="margin: 20px 0"
        id="job-artifacts"
        readOnly
        value={job.artifacts ? JSON.stringify(job.artifacts) : '{}'}
        rows={4}
        label={i18n._(t`Artifacts`)}
      />
      <ActionButtonWrapper>
        <Button
          variant="secondary"
          aria-label="close"
          component={Link}
          to="/jobs"
        >
          {i18n._(t`Close`)}
        </Button>
      </ActionButtonWrapper>
    </CardBody>
  );
}
JobDetail.propTypes = {
  job: shape({}).isRequired,
};

export default withI18n()(withRouter(JobDetail));
