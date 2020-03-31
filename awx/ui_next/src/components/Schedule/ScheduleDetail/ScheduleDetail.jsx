import React, { useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RRule, rrulestr } from 'rrule';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Schedule } from '@types';
import { Chip, ChipGroup, Title } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import CredentialChip from '@components/CredentialChip';
import { DetailList, Detail, UserDateDetail } from '@components/DetailList';
import { ScheduleOccurrences, ScheduleToggle } from '@components/Schedule';
import { formatDateString } from '@util/dates';
import useRequest from '@util/useRequest';
import { SchedulesAPI } from '@api';

const PromptTitle = styled(Title)`
  --pf-c-title--m-md--FontWeight: 700;
`;

function ScheduleDetail({ schedule, i18n }) {
  const {
    id,
    created,
    description,
    diff_mode,
    dtend,
    dtstart,
    job_tags,
    job_type,
    inventory,
    limit,
    modified,
    name,
    next_run,
    rrule,
    scm_branch,
    skip_tags,
    summary_fields,
    timezone,
  } = schedule;

  const {
    result: [credentials, preview],
    isLoading,
    error,
    request: fetchCredentialsAndPreview,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, { data: schedulePreview }] = await Promise.all([
        SchedulesAPI.readCredentials(id),
        SchedulesAPI.createPreview({
          rrule,
        }),
      ]);
      return [data.results, schedulePreview];
    }, [id, rrule]),
    []
  );

  useEffect(() => {
    fetchCredentialsAndPreview();
  }, [fetchCredentialsAndPreview]);

  const rule = rrulestr(rrule);
  const repeatFrequency =
    rule.options.freq === RRule.MINUTELY && dtstart === dtend
      ? i18n._(t`None (Run Once)`)
      : rule.toText().replace(/^\w/, c => c.toUpperCase());
  const showPromptedFields =
    (credentials && credentials.length > 0) ||
    job_type ||
    (inventory && summary_fields.inventory) ||
    scm_branch ||
    limit ||
    typeof diff_mode === 'boolean' ||
    (job_tags && job_tags.length > 0) ||
    (skip_tags && skip_tags.length > 0);

  if (isLoading) {
    return <ContentLoading />;
  }

  if (error) {
    return <ContentError error={error} />;
  }

  return (
    <CardBody>
      <ScheduleToggle schedule={schedule} css="padding-bottom: 40px" />
      <DetailList gutter="sm">
        <Detail label={i18n._(t`Name`)} value={name} />
        <Detail label={i18n._(t`Description`)} value={description} />
        <Detail
          label={i18n._(t`First Run`)}
          value={formatDateString(dtstart)}
        />
        <Detail
          label={i18n._(t`Next Run`)}
          value={formatDateString(next_run)}
        />
        <Detail label={i18n._(t`Last Run`)} value={formatDateString(dtend)} />
        <Detail label={i18n._(t`Local Time Zone`)} value={timezone} />
        <Detail label={i18n._(t`Repeat Frequency`)} value={repeatFrequency} />
        <ScheduleOccurrences preview={preview} />
        <UserDateDetail
          label={i18n._(t`Created`)}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={i18n._(t`Last Modified`)}
          date={modified}
          user={summary_fields.modified_by}
        />
        {showPromptedFields && (
          <>
            <PromptTitle size="md" css="grid-column: 1 / -1;">
              {i18n._(t`Prompted Fields`)}
            </PromptTitle>
            <Detail label={i18n._(t`Job Type`)} value={job_type} />
            {inventory && summary_fields.inventory && (
              <Detail
                label={i18n._(t`Inventory`)}
                value={
                  <Link
                    to={`/inventories/${
                      summary_fields.inventory.kind === 'smart'
                        ? 'smart_inventory'
                        : 'inventory'
                    }/${summary_fields.inventory.id}/details`}
                  >
                    {summary_fields.inventory.name}
                  </Link>
                }
              />
            )}
            <Detail label={i18n._(t`SCM Branch`)} value={scm_branch} />
            <Detail label={i18n._(t`Limit`)} value={limit} />
            {typeof diff_mode === 'boolean' && (
              <Detail
                label={i18n._(t`Show Changes`)}
                value={diff_mode ? 'On' : 'Off'}
              />
            )}
            {credentials && credentials.length > 0 && (
              <Detail
                fullWidth
                label={i18n._(t`Credentials`)}
                value={
                  <ChipGroup numChips={5}>
                    {credentials.map(c => (
                      <CredentialChip key={c.id} credential={c} isReadOnly />
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {job_tags && job_tags.length > 0 && (
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
            {skip_tags && skip_tags.length > 0 && (
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
          </>
        )}
      </DetailList>
    </CardBody>
  );
}

ScheduleDetail.propTypes = {
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleDetail);
