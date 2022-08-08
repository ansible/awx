import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { t } from '@lingui/macro';
import {
  Select,
  SelectOption,
  SelectGroup,
  SelectVariant,
  Chip,
} from '@patternfly/react-core';
import ChipGroup from 'components/ChipGroup';
import { stringIsUUID } from 'util/strings';

const JOB_URL_SEGMENT_MAP = {
  job: 'playbook',
  project_update: 'project',
  system_job: 'management',
  system: 'system_job',
  inventory_update: 'inventory',
  workflow_job: 'workflow',
};

function WorkflowOutputNavigation({ relatedJobs, parentRef }) {
  const { id } = useParams();

  const relevantResults = relatedJobs.filter(
    ({
      job: jobId,
      summary_fields: {
        unified_job_template: { unified_job_type },
      },
    }) => jobId && `${jobId}` !== id && unified_job_type !== 'workflow_approval'
  );

  const [isOpen, setIsOpen] = useState(false);
  const [filterBy, setFilterBy] = useState();
  const [sortedJobs, setSortedJobs] = useState(relevantResults);

  const handleFilter = (v) => {
    if (filterBy === v) {
      setSortedJobs(relevantResults);
      setFilterBy();
    } else {
      setFilterBy(v);
      setSortedJobs(
        relevantResults.filter(
          (node) =>
            node.summary_fields.job.status === v.toLowerCase() &&
            `${node.job}` !== id
        )
      );
    }
  };

  const numSuccessJobs = relevantResults.filter(
    (node) => node.summary_fields.job.status === 'successful'
  ).length;
  const numFailedJobs = relevantResults.length - numSuccessJobs;

  return (
    <Select
      key={`${id}`}
      variant={SelectVariant.typeaheadMulti}
      menuAppendTo={parentRef?.current}
      onToggle={() => {
        setIsOpen(!isOpen);
      }}
      selections={filterBy}
      onSelect={(e, v) => {
        if (v !== 'Failed' && v !== 'Successful') return;
        handleFilter(v);
      }}
      isOpen={isOpen}
      isGrouped
      hasInlineFilter
      placeholderText={t`Workflow Job 1/${relevantResults.length}`}
      chipGroupComponent={
        <ChipGroup numChips={1} totalChips={1}>
          <Chip key={filterBy} onClick={() => handleFilter(filterBy)}>
            {[filterBy]}
          </Chip>
        </ChipGroup>
      }
    >
      {[
        <SelectGroup label={t`Workflow Statuses`} key="status">
          <SelectOption
            description={t`Filter by failed jobs`}
            key="failed"
            value={t`Failed`}
            itemCount={numFailedJobs}
          />
          <SelectOption
            description={t`Filter by successful jobs`}
            key="successful"
            value={t`Successful`}
            itemCount={numSuccessJobs}
          />
        </SelectGroup>,
        <SelectGroup label={t`Workflow Nodes`} key="nodes">
          {sortedJobs?.map((node) => (
            <SelectOption
              key={node.id}
              to={`/jobs/${
                JOB_URL_SEGMENT_MAP[
                  node.summary_fields.unified_job_template.unified_job_type
                ]
              }/${node.summary_fields.job?.id}/output`}
              component={Link}
              value={node.summary_fields.unified_job_template.name}
            >
              {stringIsUUID(node.identifier)
                ? node.summary_fields.unified_job_template.name
                : node.identifier}
            </SelectOption>
          ))}
        </SelectGroup>,
      ]}
    </Select>
  );
}

export default WorkflowOutputNavigation;
