import React, { useCallback, useEffect, useState } from 'react';
import { Link, useHistory, useLocation } from 'react-router-dom';
import { RRule, rrulestr } from 'rrule';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Schedule } from '../../../types';
import { Chip, Title, Button } from '@patternfly/react-core';
import AlertModal from '../../../components/AlertModal';
import { CardBody, CardActionsRow } from '../../../components/Card';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import CredentialChip from '../../../components/CredentialChip';
import { DetailList, Detail, UserDateDetail } from '../../../components/DetailList';
import { ScheduleOccurrences, ScheduleToggle } from '../../../components/Schedule';
import { formatDateString } from '../../../util/dates';
import useRequest from '../../../util/useRequest';
import { SchedulesAPI } from '../../../api';
import DeleteButton from '../../../components/DeleteButton';
import ErrorDetail from '../../../components/ErrorDetail';
import ChipGroup from '../../../components/ChipGroup';

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

  const [deletionError, setDeletionError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(false);
  const history = useHistory();
  const { pathname } = useLocation();
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const handleDelete = async () => {
    setHasContentLoading(true);
    try {
      await SchedulesAPI.destroy(id);
      history.push(`${pathRoot}schedules`);
    } catch (error) {
      setDeletionError(error);
    }
    setHasContentLoading(false);
  };

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

  if (isLoading || hasContentLoading) {
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
            <Detail
              label={i18n._(t`Source Control Branch`)}
              value={scm_branch}
            />
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
                  <ChipGroup numChips={5} totalChips={credentials.length}>
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
                  <ChipGroup
                    numChips={5}
                    totalChips={job_tags.split(',').length}
                  >
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
                  <ChipGroup
                    numChips={5}
                    totalChips={skip_tags.split(',').length}
                  >
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
      <CardActionsRow>
        {summary_fields?.user_capabilities?.edit && (
          <Button
            aria-label={i18n._(t`Edit`)}
            component={Link}
            to={pathname.replace('details', 'edit')}
          >
            {i18n._(t`Edit`)}
          </Button>
        )}
        {summary_fields?.user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={i18n._(t`Delete Schedule`)}
            onConfirm={handleDelete}
          >
            {i18n._(t`Delete`)}
          </DeleteButton>
        )}
      </CardActionsRow>
      {deletionError && (
        <AlertModal
          isOpen={deletionError}
          variant="danger"
          title={i18n._(t`Error!`)}
          onClose={() => setDeletionError(null)}
        >
          {i18n._(t`Failed to delete schedule.`)}
          <ErrorDetail error={deletionError} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ScheduleDetail.propTypes = {
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleDetail);
