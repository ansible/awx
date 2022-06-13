import React, { useEffect, useCallback, useState } from 'react';
import { shape, func } from 'prop-types';

import { DateTime } from 'luxon';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { RRule } from 'rrule';
import {
  Button,
  Form,
  FormGroup,
  Title,
  ActionGroup,
  // To be removed once UI completes complex schedules
  Alert,
} from '@patternfly/react-core';
import { Config } from 'contexts/Config';
import { SchedulesAPI } from 'api';
import { dateToInputDateTime } from 'util/dates';
import useRequest from 'hooks/useRequest';
import { required } from 'util/validators';
import { parseVariableField } from 'util/yaml';
import AnsibleSelect from '../../AnsibleSelect';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import FormField, { FormSubmitError } from '../../FormField';
import {
  FormColumnLayout,
  SubFormLayout,
  FormFullWidthLayout,
} from '../../FormLayout';
import FrequencyDetailSubform from './FrequencyDetailSubform';
import SchedulePromptableFields from './SchedulePromptableFields';
import DateTimePicker from './DateTimePicker';
import buildRuleObj from './buildRuleObj';

const NUM_DAYS_PER_FREQUENCY = {
  week: 7,
  month: 31,
  year: 365,
};

const generateRunOnTheDay = (days = []) => {
  if (
    [
      RRule.MO,
      RRule.TU,
      RRule.WE,
      RRule.TH,
      RRule.FR,
      RRule.SA,
      RRule.SU,
    ].every((element) => days.indexOf(element) > -1)
  ) {
    return 'day';
  }
  if (
    [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR].every(
      (element) => days.indexOf(element) > -1
    )
  ) {
    return 'weekday';
  }
  if ([RRule.SA, RRule.SU].every((element) => days.indexOf(element) > -1)) {
    return 'weekendDay';
  }
  if (days.indexOf(RRule.MO) > -1) {
    return 'monday';
  }
  if (days.indexOf(RRule.TU) > -1) {
    return 'tuesday';
  }
  if (days.indexOf(RRule.WE) > -1) {
    return 'wednesday';
  }
  if (days.indexOf(RRule.TH) > -1) {
    return 'thursday';
  }
  if (days.indexOf(RRule.FR) > -1) {
    return 'friday';
  }
  if (days.indexOf(RRule.SA) > -1) {
    return 'saturday';
  }
  if (days.indexOf(RRule.SU) > -1) {
    return 'sunday';
  }

  return null;
};

function ScheduleFormFields({ hasDaysToKeepField, zoneOptions }) {
  const [timezone, timezoneMeta] = useField({
    name: 'timezone',
    validate: required(t`Select a value for this field`),
  });
  const [frequency, frequencyMeta] = useField({
    name: 'frequency',
    validate: required(t`Select a value for this field`),
  });
  const [{ name: dateFieldName }] = useField('startDate');
  const [{ name: timeFieldName }] = useField('startTime');
  return (
    <>
      <FormField
        id="schedule-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="schedule-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <DateTimePicker
        dateFieldName={dateFieldName}
        timeFieldName={timeFieldName}
        label={t`Start date/time`}
      />
      <FormGroup
        name="timezone"
        fieldId="schedule-timezone"
        helperTextInvalid={timezoneMeta.error}
        isRequired
        validated={
          !timezoneMeta.touched || !timezoneMeta.error ? 'default' : 'error'
        }
        label={t`Local time zone`}
      >
        <AnsibleSelect
          id="schedule-timezone"
          data={zoneOptions}
          {...timezone}
        />
      </FormGroup>
      <FormGroup
        name="frequency"
        fieldId="schedule-requency"
        helperTextInvalid={frequencyMeta.error}
        isRequired
        validated={
          !frequencyMeta.touched || !frequencyMeta.error ? 'default' : 'error'
        }
        label={t`Run frequency`}
      >
        <AnsibleSelect
          id="schedule-frequency"
          data={[
            { value: 'none', key: 'none', label: t`None (run once)` },
            { value: 'minute', key: 'minute', label: t`Minute` },
            { value: 'hour', key: 'hour', label: t`Hour` },
            { value: 'day', key: 'day', label: t`Day` },
            { value: 'week', key: 'week', label: t`Week` },
            { value: 'month', key: 'month', label: t`Month` },
            { value: 'year', key: 'year', label: t`Year` },
          ]}
          {...frequency}
        />
      </FormGroup>
      {hasDaysToKeepField ? (
        <FormField
          id="schedule-days-to-keep"
          label={t`Days of Data to Keep`}
          name="daysToKeep"
          type="number"
          validate={required(null)}
          isRequired
        />
      ) : null}
      {frequency.value !== 'none' && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {t`Frequency Details`}
          </Title>
          <FormColumnLayout>
            <FrequencyDetailSubform />
          </FormColumnLayout>
        </SubFormLayout>
      )}
    </>
  );
}

function ScheduleForm({
  hasDaysToKeepField,
  handleCancel,
  handleSubmit,
  schedule,
  submitError,
  resource,
  launchConfig,
  surveyConfig,
  resourceDefaultCredentials,
}) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isSaveDisabled, setIsSaveDisabled] = useState(false);

  let rruleError;
  const now = DateTime.now();
  const closestQuarterHour = DateTime.fromMillis(
    Math.ceil(now.ts / 900000) * 900000
  );
  const tomorrow = closestQuarterHour.plus({ days: 1 });
  const isTemplate =
    resource.type === 'workflow_job_template' ||
    resource.type === 'job_template';
  const {
    request: loadScheduleData,
    error: contentError,
    isLoading: contentLoading,
    result: { zoneOptions, credentials },
  } = useRequest(
    useCallback(async () => {
      const { data } = await SchedulesAPI.readZoneInfo();

      let creds;
      if (schedule.id) {
        const {
          data: { results },
        } = await SchedulesAPI.readCredentials(schedule.id);
        creds = results;
      }

      const zones = data.map((zone) => ({
        value: zone.name,
        key: zone.name,
        label: zone.name,
      }));

      return {
        zoneOptions: zones,
        credentials: creds || [],
      };
    }, [schedule]),
    {
      zonesOptions: [],
      credentials: [],
      isLoading: true,
    }
  );

  useEffect(() => {
    loadScheduleData();
  }, [loadScheduleData]);

  const missingRequiredInventory = useCallback(() => {
    let missingInventory = false;
    if (
      launchConfig.inventory_needed_to_start &&
      !schedule?.summary_fields?.inventory?.id
    ) {
      missingInventory = true;
    }
    return missingInventory;
  }, [launchConfig, schedule]);

  const hasMissingSurveyValue = useCallback(() => {
    let missingValues = false;
    if (launchConfig?.survey_enabled) {
      surveyConfig.spec.forEach((question) => {
        const hasDefaultValue = Boolean(question.default);
        const hasSchedule = Object.keys(schedule).length;
        const isRequired = question.required;
        if (isRequired && !hasDefaultValue) {
          if (!hasSchedule) {
            missingValues = true;
          } else {
            const hasMatchingKey = Object.keys(schedule?.extra_data).includes(
              question.variable
            );
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
        }
      });
    }
    return missingValues;
  }, [launchConfig, schedule, surveyConfig]);

  const hasCredentialsThatPrompt = useCallback(() => {
    if (launchConfig?.ask_credential_on_launch) {
      if (Object.keys(schedule).length > 0) {
        const defaultCredsWithoutOverrides = [];

        const credentialHasOverride = (templateDefaultCred) => {
          let hasOverride = false;
          credentials.forEach((nodeCredential) => {
            if (
              templateDefaultCred.credential_type ===
              nodeCredential.credential_type
            ) {
              if (
                (!templateDefaultCred.vault_id &&
                  !nodeCredential.inputs.vault_id) ||
                (templateDefaultCred.vault_id &&
                  nodeCredential.inputs.vault_id &&
                  templateDefaultCred.vault_id ===
                    nodeCredential.inputs.vault_id)
              ) {
                hasOverride = true;
              }
            }
          });

          return hasOverride;
        };

        if (resourceDefaultCredentials) {
          resourceDefaultCredentials.forEach((defaultCred) => {
            if (!credentialHasOverride(defaultCred)) {
              defaultCredsWithoutOverrides.push(defaultCred);
            }
          });
        }

        return (
          credentials
            .concat(defaultCredsWithoutOverrides)
            .filter((credential) => {
              let credentialRequiresPass = false;

              Object.entries(credential.inputs).forEach(([key, value]) => {
                if (key !== 'vault_id' && value === 'ASK') {
                  credentialRequiresPass = true;
                }
              });

              return credentialRequiresPass;
            }).length > 0
        );
      }

      return launchConfig?.defaults?.credentials
        ? launchConfig.defaults.credentials.filter(
            (credential) => credential?.passwords_needed.length > 0
          ).length > 0
        : false;
    }

    return false;
  }, [launchConfig, schedule, credentials, resourceDefaultCredentials]);

  useEffect(() => {
    if (
      isTemplate &&
      (missingRequiredInventory() ||
        hasMissingSurveyValue() ||
        hasCredentialsThatPrompt())
    ) {
      setIsSaveDisabled(true);
    }
  }, [
    isTemplate,
    hasMissingSurveyValue,
    missingRequiredInventory,
    hasCredentialsThatPrompt,
  ]);

  let showPromptButton = false;

  if (
    launchConfig &&
    (launchConfig.ask_inventory_on_launch ||
      launchConfig.ask_variables_on_launch ||
      launchConfig.ask_job_type_on_launch ||
      launchConfig.ask_limit_on_launch ||
      launchConfig.ask_credential_on_launch ||
      launchConfig.ask_scm_branch_on_launch ||
      launchConfig.ask_tags_on_launch ||
      launchConfig.ask_skip_tags_on_launch ||
      launchConfig.survey_enabled ||
      launchConfig.inventory_needed_to_start ||
      launchConfig.variables_needed_to_start?.length > 0)
  ) {
    showPromptButton = true;
  }
  const [currentDate, time] = dateToInputDateTime(closestQuarterHour.toISO());

  const [tomorrowDate] = dateToInputDateTime(tomorrow.toISO());
  const initialValues = {
    daysOfWeek: [],
    description: schedule.description || '',
    end: 'never',
    endDate: tomorrowDate,
    endTime: time,
    frequency: 'none',
    interval: 1,
    name: schedule.name || '',
    occurrences: 1,
    runOn: 'day',
    runOnDayMonth: 1,
    runOnDayNumber: 1,
    runOnTheDay: 'sunday',
    runOnTheMonth: 1,
    runOnTheOccurrence: 1,
    startDate: currentDate,
    startTime: time,
    timezone: schedule.timezone || 'America/New_York',
  };
  const submitSchedule = (
    values,
    launchConfiguration,
    surveyConfiguration,
    scheduleCredentials
  ) => {
    handleSubmit(
      values,
      launchConfiguration,
      surveyConfiguration,
      scheduleCredentials
    );
  };

  if (hasDaysToKeepField) {
    let initialDaysToKeep = 30;
    if (schedule?.extra_data) {
      if (
        typeof schedule?.extra_data === 'string' &&
        schedule?.extra_data !== ''
      ) {
        initialDaysToKeep = parseVariableField(schedule?.extra_data).days;
      }
      if (typeof schedule?.extra_data === 'object') {
        initialDaysToKeep = schedule?.extra_data?.days;
      }
    }
    initialValues.daysToKeep = initialDaysToKeep;
  }

  const overriddenValues = {};

  if (Object.keys(schedule).length > 0) {
    if (schedule.rrule) {
      if (schedule.rrule.split(/\s+/).length > 2) {
        return (
          <Form autoComplete="off">
            <Alert
              variant="danger"
              isInline
              ouiaId="form-submit-error-alert"
              title={t`Complex schedules are not supported in the UI yet, please use the API to manage this schedule.`}
            />
            <b>{t`Schedule Rules`}:</b>
            <pre css="white-space: pre; font-family: var(--pf-global--FontFamily--monospace)">
              {schedule.rrule}
            </pre>
            <ActionGroup>
              <Button
                ouiaId="schedule-form-cancel-button"
                aria-label={t`Cancel`}
                variant="secondary"
                type="button"
                onClick={handleCancel}
              >
                {t`Cancel`}
              </Button>
            </ActionGroup>
          </Form>
        );
      }

      try {
        const {
          origOptions: {
            bymonth,
            bymonthday,
            bysetpos,
            byweekday,
            count,
            dtstart,
            freq,
            interval,
          },
        } = RRule.fromString(schedule.rrule.replace(' ', '\n'));

        if (dtstart) {
          const [startDate, startTime] = dateToInputDateTime(
            schedule.dtstart,
            schedule.timezone
          );

          overriddenValues.startDate = startDate;
          overriddenValues.startTime = startTime;
        }

        if (schedule.until) {
          overriddenValues.end = 'onDate';

          const [endDate, endTime] = dateToInputDateTime(
            schedule.until,
            schedule.timezone
          );

          overriddenValues.endDate = endDate;
          overriddenValues.endTime = endTime;
        } else if (count) {
          overriddenValues.end = 'after';
          overriddenValues.occurrences = count;
        }

        if (interval) {
          overriddenValues.interval = interval;
        }

        if (typeof freq === 'number') {
          switch (freq) {
            case RRule.MINUTELY:
              if (schedule.dtstart !== schedule.dtend) {
                overriddenValues.frequency = 'minute';
              }
              break;
            case RRule.HOURLY:
              overriddenValues.frequency = 'hour';
              break;
            case RRule.DAILY:
              overriddenValues.frequency = 'day';
              break;
            case RRule.WEEKLY:
              overriddenValues.frequency = 'week';
              if (byweekday) {
                overriddenValues.daysOfWeek = byweekday;
              }
              break;
            case RRule.MONTHLY:
              overriddenValues.frequency = 'month';
              if (bymonthday) {
                overriddenValues.runOnDayNumber = bymonthday;
              } else if (bysetpos) {
                overriddenValues.runOn = 'the';
                overriddenValues.runOnTheOccurrence = bysetpos;
                overriddenValues.runOnTheDay = generateRunOnTheDay(byweekday);
              }
              break;
            case RRule.YEARLY:
              overriddenValues.frequency = 'year';
              if (bymonthday) {
                overriddenValues.runOnDayNumber = bymonthday;
                overriddenValues.runOnDayMonth = bymonth;
              } else if (bysetpos) {
                overriddenValues.runOn = 'the';
                overriddenValues.runOnTheOccurrence = bysetpos;
                overriddenValues.runOnTheDay = generateRunOnTheDay(byweekday);
                overriddenValues.runOnTheMonth = bymonth;
              }
              break;
            default:
              break;
          }
        }
      } catch (error) {
        rruleError = error;
      }
    } else {
      rruleError = new Error(t`Schedule is missing rrule`);
    }
  }

  if (contentError || rruleError) {
    return <ContentError error={contentError || rruleError} />;
  }

  if (contentLoading) {
    return <ContentLoading />;
  }

  return (
    <Config>
      {() => (
        <Formik
          initialValues={Object.assign(initialValues, overriddenValues)}
          onSubmit={(values) => {
            submitSchedule(values, launchConfig, surveyConfig, credentials);
          }}
          validate={(values) => {
            const errors = {};
            const {
              end,
              endDate,
              frequency,
              runOn,
              runOnDayNumber,
              startDate,
            } = values;

            if (
              end === 'onDate' &&
              DateTime.fromISO(endDate)
                .diff(DateTime.fromISO(startDate), 'days')
                .toObject().days < NUM_DAYS_PER_FREQUENCY[frequency]
            ) {
              const rule = new RRule(buildRuleObj(values));
              if (rule.all().length === 0) {
                errors.startDate = t`Selected date range must have at least 1 schedule occurrence.`;
                errors.endDate = t`Selected date range must have at least 1 schedule occurrence.`;
              }
            }

            if (
              end === 'onDate' &&
              DateTime.fromISO(startDate) >= DateTime.fromISO(endDate)
            ) {
              errors.endDate = t`Please select an end date/time that comes after the start date/time.`;
            }

            if (
              (frequency === 'month' || frequency === 'year') &&
              runOn === 'day' &&
              (runOnDayNumber < 1 || runOnDayNumber > 31)
            ) {
              errors.runOn = t`Please select a day number between 1 and 31.`;
            }
            return errors;
          }}
        >
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <ScheduleFormFields
                  hasDaysToKeepField={hasDaysToKeepField}
                  zoneOptions={zoneOptions}
                />
                {isWizardOpen && (
                  <SchedulePromptableFields
                    schedule={schedule}
                    credentials={credentials}
                    surveyConfig={surveyConfig}
                    launchConfig={launchConfig}
                    resource={resource}
                    onCloseWizard={() => {
                      setIsWizardOpen(false);
                    }}
                    onSave={() => {
                      setIsWizardOpen(false);
                      setIsSaveDisabled(false);
                    }}
                    resourceDefaultCredentials={resourceDefaultCredentials}
                  />
                )}
                <FormSubmitError error={submitError} />
                <FormFullWidthLayout>
                  <ActionGroup>
                    <Button
                      ouiaId="schedule-form-save-button"
                      aria-label={t`Save`}
                      variant="primary"
                      type="button"
                      onClick={formik.handleSubmit}
                      isDisabled={isSaveDisabled}
                    >
                      {t`Save`}
                    </Button>

                    {isTemplate && showPromptButton && (
                      <Button
                        ouiaId="schedule-form-prompt-button"
                        variant="secondary"
                        type="button"
                        aria-label={t`Prompt`}
                        onClick={() => setIsWizardOpen(true)}
                      >
                        {t`Prompt`}
                      </Button>
                    )}
                    <Button
                      ouiaId="schedule-form-cancel-button"
                      aria-label={t`Cancel`}
                      variant="secondary"
                      type="button"
                      onClick={handleCancel}
                    >
                      {t`Cancel`}
                    </Button>
                  </ActionGroup>
                </FormFullWidthLayout>
              </FormColumnLayout>
            </Form>
          )}
        </Formik>
      )}
    </Config>
  );
}

ScheduleForm.propTypes = {
  handleCancel: func.isRequired,
  handleSubmit: func.isRequired,
  schedule: shape({}),
  submitError: shape(),
};

ScheduleForm.defaultProps = {
  schedule: {},
  submitError: null,
};

export default ScheduleForm;
