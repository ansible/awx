import 'styled-components/macro';
import React, { useCallback, useEffect } from 'react';
import { Link, useHistory, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { t } from '@lingui/macro';
import { Chip, Divider, Title, Button } from '@patternfly/react-core';
import { Schedule } from 'types';
import { formatDateString } from 'util/dates';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import { JobTemplatesAPI, SchedulesAPI, WorkflowJobTemplatesAPI } from 'api';
import { parseVariableField, jsonToYaml } from 'util/yaml';
import { useConfig } from 'contexts/Config';
import parseRuleObj from '../shared/parseRuleObj';
import FrequencyDetails from './FrequencyDetails';
import AlertModal from '../../AlertModal';
import { CardBody, CardActionsRow } from '../../Card';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import CredentialChip from '../../CredentialChip';
import { DetailList, Detail, UserDateDetail } from '../../DetailList';
import ScheduleOccurrences from '../ScheduleOccurrences';
import ScheduleToggle from '../ScheduleToggle';
import DeleteButton from '../../DeleteButton';
import ErrorDetail from '../../ErrorDetail';
import ChipGroup from '../../ChipGroup';
import { VariablesDetail } from '../../CodeEditor';
import { VERBOSITY } from '../../VerbositySelectField';
import helpText from '../../../screens/Template/shared/JobTemplate.helptext';

const PromptDivider = styled(Divider)`
  margin-top: var(--pf-global--spacer--lg);
  margin-bottom: var(--pf-global--spacer--lg);
`;

const PromptTitle = styled(Title)`
  margin-top: 40px;
  --pf-c-title--m-md--FontWeight: 700;
  grid-column: 1 / -1;
`;

const PromptDetailList = styled(DetailList)`
  padding: 0px 20px;
`;

const FrequencyDetailsContainer = styled.div`
  background-color: var(--pf-global--palette--black-150);
  margin-top: var(--pf-global--spacer--lg);
  margin-bottom: var(--pf-global--spacer--lg);
  margin-right: calc(var(--pf-c-card--child--PaddingRight) * -1);
  margin-left: calc(var(--pf-c-card--child--PaddingLeft) * -1);
  padding: var(--pf-c-card--child--PaddingRight);

  & > p {
    margin-bottom: var(--pf-global--spacer--md);
  }

  & > *:not(:first-child):not(:last-child) {
    margin-bottom: var(--pf-global--spacer--md);
    padding-bottom: var(--pf-global--spacer--md);
    border-bottom: 1px solid var(--pf-global--palette--black-300);
  }

  & + & {
    margin-top: calc(var(--pf-global--spacer--lg) * -1);
  }
`;

function ScheduleDetail({ hasDaysToKeepField, schedule, surveyConfig }) {
  const {
    id,
    created,
    description,
    diff_mode,
    dtend,
    dtstart,
    extra_data,
    inventory,
    job_tags,
    job_type,
    limit,
    modified,
    name,
    next_run,
    rrule,
    scm_branch,
    skip_tags,
    summary_fields,
    timezone,
    verbosity,
  } = schedule;

  const history = useHistory();
  const { pathname } = useLocation();
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));
  const config = useConfig();

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
    result: [credentials, preview, launchData],
    isLoading,
    error: readContentError,
    request: fetchCredentialsAndPreview,
  } = useRequest(
    useCallback(async () => {
      const promises = [
        SchedulesAPI.readCredentials(id),
        SchedulesAPI.createPreview({
          rrule,
        }),
      ];

      if (
        schedule?.summary_fields?.unified_job_template?.unified_job_type ===
        'job'
      ) {
        promises.push(
          JobTemplatesAPI.readLaunch(
            schedule.summary_fields.unified_job_template.id
          )
        );
      } else if (
        schedule?.summary_fields?.unified_job_template?.unified_job_type ===
        'workflow_job'
      ) {
        promises.push(
          WorkflowJobTemplatesAPI.readLaunch(
            schedule.summary_fields.unified_job_template.id
          )
        );
      } else {
        promises.push(Promise.resolve());
      }

      const [{ data }, { data: schedulePreview }, launch] = await Promise.all(
        promises
      );

      return [data.results, schedulePreview, launch?.data];
    }, [id, schedule, rrule]),
    []
  );

  useEffect(() => {
    fetchCredentialsAndPreview();
  }, [fetchCredentialsAndPreview]);

  const frequencies = {
    minute: t`Minute`,
    hour: t`Hour`,
    day: t`Day`,
    week: t`Week`,
    month: t`Month`,
    year: t`Year`,
  };
  const { frequency, frequencyOptions, exceptionFrequency, exceptionOptions } =
    parseRuleObj(schedule);
  const repeatFrequency = frequency.length
    ? frequency.map((f) => frequencies[f]).join(', ')
    : t`None (Run Once)`;
  const exceptionRepeatFrequency = exceptionFrequency.length
    ? exceptionFrequency.map((f) => frequencies[f]).join(', ')
    : t`None (Run Once)`;

  const {
    ask_credential_on_launch,
    inventory_needed_to_start,
    ask_diff_mode_on_launch,
    ask_inventory_on_launch,
    ask_job_type_on_launch,
    ask_limit_on_launch,
    ask_scm_branch_on_launch,
    ask_skip_tags_on_launch,
    ask_tags_on_launch,
    ask_variables_on_launch,
    ask_verbosity_on_launch,
    survey_enabled,
  } = launchData || {};

  const missingRequiredInventory = () => {
    if (!inventory_needed_to_start || schedule?.summary_fields?.inventory?.id) {
      return false;
    }
    return true;
  };

  const hasMissingSurveyValue = () => {
    let missingValues = false;
    if (survey_enabled) {
      surveyConfig.spec.forEach((question) => {
        const hasDefaultValue = Boolean(question.default);
        if (question.required && !hasDefaultValue) {
          const extraDataKeys = Object.keys(schedule?.extra_data);

          const hasMatchingKey = extraDataKeys.includes(question.variable);
          Object.values(schedule?.extra_data).forEach((value) => {
            if (!value || !hasMatchingKey) {
              missingValues = true;
            } else {
              missingValues = false;
            }
          });
          if (!Object.values(schedule.extra_data).length) {
            missingValues = true;
          }
        }
      });
    }
    return missingValues;
  };
  const isDisabled = Boolean(
    missingRequiredInventory() || hasMissingSurveyValue()
  );

  const showCredentialsDetail =
    ask_credential_on_launch && credentials.length > 0;
  const showInventoryDetail = ask_inventory_on_launch && inventory;
  const showVariablesDetail =
    (ask_variables_on_launch || survey_enabled) &&
    ((typeof extra_data === 'string' && extra_data !== '') ||
      (typeof extra_data === 'object' && Object.keys(extra_data).length > 0));
  const showTagsDetail = ask_tags_on_launch && job_tags && job_tags.length > 0;
  const showSkipTagsDetail =
    ask_skip_tags_on_launch && skip_tags && skip_tags.length > 0;
  const showDiffModeDetail =
    ask_diff_mode_on_launch && typeof diff_mode === 'boolean';
  const showLimitDetail = ask_limit_on_launch && limit;
  const showJobTypeDetail = ask_job_type_on_launch && job_type;
  const showSCMBranchDetail = ask_scm_branch_on_launch && scm_branch;
  const showVerbosityDetail = ask_verbosity_on_launch && VERBOSITY()[verbosity];

  const showPromptedFields =
    showCredentialsDetail ||
    showDiffModeDetail ||
    showInventoryDetail ||
    showJobTypeDetail ||
    showLimitDetail ||
    showSCMBranchDetail ||
    showSkipTagsDetail ||
    showTagsDetail ||
    showVerbosityDetail ||
    showVariablesDetail;

  if (isLoading) {
    return <ContentLoading />;
  }

  if (readContentError) {
    return <ContentError error={readContentError} />;
  }

  let daysToKeep = null;
  if (hasDaysToKeepField && extra_data) {
    if (typeof extra_data === 'string' && extra_data !== '') {
      daysToKeep = parseVariableField(extra_data).days;
    }
    if (typeof extra_data === 'object') {
      daysToKeep = extra_data?.days;
    }
  }

  return (
    <CardBody>
      <ScheduleToggle
        schedule={schedule}
        css="padding-bottom: 40px"
        isDisabled={isDisabled}
      />
      <DetailList gutter="sm">
        <Detail label={t`Name`} value={name} />
        <Detail label={t`Description`} value={description} />
        <Detail
          label={t`First Run`}
          value={formatDateString(dtstart, timezone)}
        />
        <Detail
          label={t`Next Run`}
          value={formatDateString(next_run, timezone)}
        />
        <Detail label={t`Last Run`} value={formatDateString(dtend, timezone)} />
        <Detail
          label={t`Local Time Zone`}
          value={timezone}
          helpText={helpText.localTimeZone(config)}
        />
        <Detail label={t`Repeat Frequency`} value={repeatFrequency} />
        <Detail
          label={t`Exception Frequency`}
          value={exceptionRepeatFrequency}
        />
      </DetailList>
      {frequency.length ? (
        <FrequencyDetailsContainer>
          <p>
            <strong>{t`Frequency Details`}</strong>
          </p>
          {frequency.map((freq) => (
            <FrequencyDetails
              key={freq}
              type={freq}
              label={frequencies[freq]}
              options={frequencyOptions[freq]}
              timezone={timezone}
            />
          ))}
        </FrequencyDetailsContainer>
      ) : null}
      {exceptionFrequency.length ? (
        <FrequencyDetailsContainer>
          <p css="border-top: 0">
            <strong>{t`Frequency Exception Details`}</strong>
          </p>
          {exceptionFrequency.map((freq) => (
            <FrequencyDetails
              key={freq}
              type={freq}
              label={frequencies[freq]}
              options={exceptionOptions[freq]}
              timezone={timezone}
              isException
            />
          ))}
        </FrequencyDetailsContainer>
      ) : null}
      <DetailList gutter="sm">
        {hasDaysToKeepField ? (
          <Detail label={t`Days of Data to Keep`} value={daysToKeep} />
        ) : null}
        <ScheduleOccurrences preview={preview} tz={timezone} />
        <UserDateDetail
          label={t`Created`}
          date={created}
          user={summary_fields.created_by}
        />
        <UserDateDetail
          label={t`Last Modified`}
          date={modified}
          user={summary_fields.modified_by}
        />
      </DetailList>
      {showPromptedFields && (
        <>
          <PromptTitle headingLevel="h2">{t`Prompted Values`}</PromptTitle>
          <PromptDivider />
          <PromptDetailList>
            {ask_job_type_on_launch && (
              <Detail label={t`Job Type`} value={job_type} />
            )}
            {showInventoryDetail && (
              <Detail
                label={t`Inventory`}
                value={
                  summary_fields?.inventory ? (
                    <Link
                      to={`/inventories/${
                        summary_fields?.inventory?.kind === 'smart'
                          ? 'smart_inventory'
                          : 'inventory'
                      }/${summary_fields?.inventory?.id}/details`}
                    >
                      {summary_fields?.inventory?.name}
                    </Link>
                  ) : (
                    ' '
                  )
                }
              />
            )}
            {ask_verbosity_on_launch && (
              <Detail label={t`Verbosity`} value={VERBOSITY()[verbosity]} />
            )}
            {ask_scm_branch_on_launch && (
              <Detail label={t`Source Control Branch`} value={scm_branch} />
            )}
            {ask_limit_on_launch && <Detail label={t`Limit`} value={limit} />}
            {showDiffModeDetail && (
              <Detail
                label={t`Show Changes`}
                value={diff_mode ? t`On` : t`Off`}
              />
            )}
            {showCredentialsDetail && (
              <Detail
                fullWidth
                label={t`Credentials`}
                value={
                  <ChipGroup
                    numChips={5}
                    totalChips={credentials.length}
                    ouiaId="schedule-credential-chips"
                  >
                    {credentials.map((c) => (
                      <CredentialChip
                        key={c.id}
                        credential={c}
                        isReadOnly
                        ouiaId={`credential-${c.id}-chip`}
                      />
                    ))}
                  </ChipGroup>
                }
              />
            )}
            {showTagsDetail && (
              <Detail
                fullWidth
                label={t`Job Tags`}
                value={
                  <ChipGroup
                    numChips={5}
                    totalChips={job_tags.split(',').length}
                    ouiaId="schedule-job-tag-chips"
                  >
                    {job_tags.split(',').map((jobTag) => (
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
            {showSkipTagsDetail && (
              <Detail
                fullWidth
                label={t`Skip Tags`}
                value={
                  <ChipGroup
                    numChips={5}
                    totalChips={skip_tags.split(',').length}
                    ouiaId="schedule-skip-tag-chips"
                  >
                    {skip_tags.split(',').map((skipTag) => (
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
            {showVariablesDetail && (
              <VariablesDetail
                value={jsonToYaml(JSON.stringify(extra_data))}
                rows={4}
                label={t`Variables`}
                name="extra_vars"
                dataCy="schedule-detail-variables"
              />
            )}
          </PromptDetailList>
        </>
      )}
      <CardActionsRow>
        {summary_fields?.user_capabilities?.edit && (
          <Button
            ouiaId="schedule-detail-edit-button"
            aria-label={t`Edit`}
            component={Link}
            to={pathname.replace('details', 'edit')}
          >
            {t`Edit`}
          </Button>
        )}
        {summary_fields?.user_capabilities?.delete && (
          <DeleteButton
            name={name}
            modalTitle={t`Delete Schedule`}
            onConfirm={deleteSchedule}
            isDisabled={isDeleteLoading}
          >
            {t`Delete`}
          </DeleteButton>
        )}
      </CardActionsRow>
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={t`Error!`}
          onClose={dismissError}
        >
          {t`Failed to delete schedule.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </CardBody>
  );
}

ScheduleDetail.propTypes = {
  schedule: Schedule.isRequired,
};

export default ScheduleDetail;
