import React, { Component, useState, useEffect } from 'react';
import { Link, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CardBody, Button } from '@patternfly/react-core';
import styled from 'styled-components';
import { DetailList, Detail } from '@components/DetailList';
import { ChipGroup, Chip } from '@components/Chip';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
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

function JobDetail ({ job, i18n }) {
  const [instanceGroups, setInstanceGroups] = useState(null);
  console.log(job);
  const {
    job_template: jobTemplate,
    project,
    inventory,
    instance_group: instanceGroup,
  } = job.summary_fields;

  return (
    <CardBody>
      <DetailList>
        {/* TODO: add status icon? */}
        <Detail
          label={i18n._(t`Status`)}
          value={toTitleCase(job.status)}
        />
        <Detail
          label={i18n._(t`Started`)}
          value={job.started}
        />
        <Detail
          label={i18n._(t`Finished`)}
          value={job.finished}
        />
        <Detail
          label={i18n._(t`Template`)}
          value={(
            <Link to={`/templates/job_template/${jobTemplate.id}`}>
              {jobTemplate.name}
            </Link>
          )}
        />
        <Detail
          label={i18n._(t`Job Type`)}
          value={toTitleCase(job.job_type)}
        />
        <Detail
          label={i18n._(t`Inventory`)}
          value={(
            <Link to={`/inventory/${inventory.id}`}>
              {inventory.name}
            </Link>
          )}
        />
        {/* TODO: show project status icon */}
        <Detail
          label={i18n._(t`Project`)}
          value={(
            <Link to={`/projects/${project.id}`}>
              {project.name}
            </Link>
          )}
        />
        <Detail
          label={i18n._(t`Revision`)}
          value={job.scm_revision}
        />
        <Detail
          label={i18n._(t`Playbook`)}
          value={null}
        />
        <Detail
          label={i18n._(t`Limit`)}
          value={job.limit}
        />
        <Detail
          label={i18n._(t`Verbosity`)}
          value={VERBOSITY[job.verbosity]}
        />
        <Detail
          label={i18n._(t`Environment`)}
          value={null}
        />
        <Detail
          label={i18n._(t`Execution Node`)}
          value={job.exucution_node}
        />
        <Detail
          label={i18n._(t`Instance Group`)}
          value={(
            <Link to={`/instance_groups/${instanceGroup.id}`}>
              {instanceGroup.name}
            </Link>
          )}
        />
        <Detail
          label={i18n._(t`Job Slice`)}
          value={`${job.job_slice_number}/${job.job_slice_count}`}
        />
        {(instanceGroups && instanceGroups.length > 0) && (
          <Detail
            fullWidth
            label={i18n._(t`Instance Groups`)}
            value={(
              <ChipGroup showOverflowAfter={5}>
                {instanceGroups.map(ig => (
                  <Chip key={ig.id} isReadOnly>{ig.name}</Chip>
                ))}
              </ChipGroup>
            )}
          />
        )}
      </DetailList>
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

export default withI18n()(withRouter(JobDetail));
