import 'styled-components/macro';
import React, { useCallback, useEffect } from 'react';
import { Link, useHistory, useLocation } from 'react-router-dom';
import { RRule, rrulestr } from 'rrule';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Chip, Title, Button } from '@patternfly/react-core';
import { Schedule } from '../../../types';
import AlertModal from '../../AlertModal';
import { CardBody, CardActionsRow } from '../../Card';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import CredentialChip from '../../CredentialChip';
import { DetailList, Detail, UserDateDetail } from '../../DetailList';
import ScheduleOccurrences from '../ScheduleOccurrences';
import ScheduleToggle from '../ScheduleToggle';
import { formatDateString } from '../../../util/dates';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import { SchedulesAPI } from '../../../api';
import DeleteButton from '../../DeleteButton';
import ErrorDetail from '../../ErrorDetail';
import ChipGroup from '../../ChipGroup';

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

  const history = useHistory();
  const { pathname } = useLocation();
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const {
    request: deleteSchedule,
    isLoading: isDeleteLoading,
    error: deleteError,
  } = useRequest(
    useCallback(async () => {
      await SchedulesAPI.destroy(id);
      history.push(`${pathRoot}schedules`);
    }, [id, history, pathRoot])
  );

  const { error, dismissError } = useDismissableError(deleteError);

  const {
    result: [credentials, preview],
    isLoading,
    error: readContentError,
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

  if (readContentError) {
    return <ContentError error={readContentError} />;
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
            onConfirm={deleteSchedule}
            isDisabled={isDeleteLoading}
          >
            {i18n._(t`Delete`)}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to delete schedule.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ScheduleDetail.propTypes = {
  schedule: Schedule.isRequired,
};

export default withI18n()(ScheduleDetail);
