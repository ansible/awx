import React, { useEffect, useCallback, useState } from 'react';
import { shape, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { RRule } from 'rrule';
import {
  Button,
  Form,
  FormGroup,
  Title,
  ActionGroup,
} from '@patternfly/react-core';
import { Config } from '../../../contexts/Config';
import { SchedulesAPI } from '../../../api';
import AnsibleSelect from '../../AnsibleSelect';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import FormField, { FormSubmitError } from '../../FormField';
import {
  FormColumnLayout,
  SubFormLayout,
  FormFullWidthLayout,
} from '../../FormLayout';
import { dateToInputDateTime, formatDateStringUTC } from '../../../util/dates';
import useRequest from '../../../util/useRequest';
import { required } from '../../../util/validators';
import { parseVariableField } from '../../../util/yaml';
import FrequencyDetailSubform from './FrequencyDetailSubform';
import SchedulePromptableFields from './SchedulePromptableFields';

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
    ].every(element => days.indexOf(element) > -1)
  ) {
    return 'day';
  }
  if (
    [RRule.MO, RRule.TU, RRule.WE, RRule.TH, RRule.FR].every(
      element => days.indexOf(element) > -1
    )
  ) {
    return 'weekday';
  }
  if ([RRule.SA, RRule.SU].every(element => days.indexOf(element) > -1)) {
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

function ScheduleFormFields({ i18n, hasDaysToKeepField, zoneOptions }) {
  const [startDateTime, startDateTimeMeta] = useField({
    name: 'startDateTime',
    validate: required(
      i18n._(t`Select a valid date and time for this field`),
      i18n
    ),
  });
  const [timezone, timezoneMeta] = useField({
    name: 'timezone',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [frequency, frequencyMeta] = useField({
    name: 'frequency',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  return (
    <>
      <FormField
        id="schedule-name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="schedule-description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <FormGroup
        fieldId="schedule-start-datetime"
        helperTextInvalid={startDateTimeMeta.error}
        isRequired
        validated={
          !startDateTimeMeta.touched || !startDateTimeMeta.error
            ? 'default'
            : 'error'
        }
        label={i18n._(t`Start date/time`)}
      >
        <input
          className="pf-c-form-control"
          type="datetime-local"
          id="schedule-start-datetime"
          step="1"
          {...startDateTime}
        />
      </FormGroup>
      <FormGroup
        name="timezone"
        fieldId="schedule-timezone"
        helperTextInvalid={timezoneMeta.error}
        isRequired
        validated={
          !timezoneMeta.touched || !timezoneMeta.error ? 'default' : 'error'
        }
        label={i18n._(t`Local time zone`)}
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
        label={i18n._(t`Run frequency`)}
      >
        <AnsibleSelect
          id="schedule-frequency"
          data={[
            { value: 'none', key: 'none', label: i18n._(t`None (run once)`) },
            { value: 'minute', key: 'minute', label: i18n._(t`Minute`) },
            { value: 'hour', key: 'hour', label: i18n._(t`Hour`) },
            { value: 'day', key: 'day', label: i18n._(t`Day`) },
            { value: 'week', key: 'week', label: i18n._(t`Week`) },
            { value: 'month', key: 'month', label: i18n._(t`Month`) },
            { value: 'year', key: 'year', label: i18n._(t`Year`) },
          ]}
          {...frequency}
        />
      </FormGroup>
      {hasDaysToKeepField ? (
        <FormField
          id="schedule-days-to-keep"
          label={i18n._(t`Days of Data to Keep`)}
          name="daysToKeep"
          type="number"
          validate={required(null, i18n)}
          isRequired
        />
      ) : null}
      {frequency.value !== 'none' && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {i18n._(t`Frequency Details`)}
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
  i18n,
  schedule,
  submitError,
  resource,
  launchConfig,
  surveyConfig,
  ...rest
}) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isSaveDisabled, setIsSaveDisabled] = useState(false);

  let rruleError;
  const now = new Date();
  const closestQuarterHour = new Date(
    Math.ceil(now.getTime() / 900000) * 900000
  );
  const tomorrow = new Date(closestQuarterHour);
  tomorrow.setDate(tomorrow.getDate() + 1);

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

      const zones = data.map(zone => {
        return {
          value: zone.name,
          key: zone.name,
          label: zone.name,
        };
      });

      return {
        zoneOptions: zones,
        credentials: creds || [],
      };
    }, [schedule]),
    {
      zonesOptions: [],
      credentials: [],
    }
  );
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
      surveyConfig.spec.forEach(question => {
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
            Object.values(schedule?.extra_data).forEach(value => {
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

  useEffect(() => {
    if (isTemplate && (missingRequiredInventory() || hasMissingSurveyValue())) {
      setIsSaveDisabled(true);
    }
  }, [isTemplate, hasMissingSurveyValue, missingRequiredInventory]);

  useEffect(() => {
    loadScheduleData();
  }, [loadScheduleData]);

  let showPromptButton = false;

  if (
    launchConfig &&
    (launchConfig.ask_inventory_on_launch ||
      launchConfig.ask_variables_on_launch ||
      launchConfig.ask_job_type_on_launch ||
      launchConfig.ask_limit_on_launch ||
      launchConfig.ask_credential_on_launch ||
      launchConfig.ask_scm_branch_on_launch ||
      launchConfig.survey_enabled ||
      launchConfig.inventory_needed_to_start ||
      launchConfig.variables_needed_to_start?.length > 0)
  ) {
    showPromptButton = true;
  }

  const initialValues = {
    daysOfWeek: [],
    description: schedule.description || '',
    end: 'never',
    endDateTime: dateToInputDateTime(tomorrow),
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
    startDateTime: dateToInputDateTime(closestQuarterHour),
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
          overriddenValues.startDateTime = dateToInputDateTime(
            new Date(formatDateStringUTC(dtstart))
          );
        }

        if (schedule.until) {
          overriddenValues.end = 'onDate';
          overriddenValues.endDateTime = schedule.until;
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
      rruleError = new Error(i18n._(t`Schedule is missing rrule`));
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
      {() => {
        return (
          <Formik
            initialValues={Object.assign(initialValues, overriddenValues)}
            onSubmit={values => {
              submitSchedule(values, launchConfig, surveyConfig, credentials);
            }}
            validate={values => {
              const errors = {};
              const {
                end,
                endDateTime,
                frequency,
                runOn,
                runOnDayNumber,
                startDateTime,
              } = values;

              if (
                end === 'onDate' &&
                new Date(startDateTime) > new Date(endDateTime)
              ) {
                errors.endDateTime = i18n._(
                  t`Please select an end date/time that comes after the start date/time.`
                );
              }

              if (
                (frequency === 'month' || frequency === 'year') &&
                runOn === 'day' &&
                (runOnDayNumber < 1 || runOnDayNumber > 31)
              ) {
                errors.runOn = i18n._(
                  t`Please select a day number between 1 and 31.`
                );
              }

              return errors;
            }}
          >
            {formik => (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
                  <ScheduleFormFields
                    hasDaysToKeepField={hasDaysToKeepField}
                    i18n={i18n}
                    zoneOptions={zoneOptions}
                    {...rest}
                  />
                  {isWizardOpen && (
                    <SchedulePromptableFields
                      schedule={schedule}
                      credentials={credentials}
                      surveyConfig={surveyConfig}
                      launchConfig={launchConfig}
                      resource={resource}
                      onCloseWizard={hasErrors => {
                        setIsWizardOpen(false);
                        setIsSaveDisabled(hasErrors);
                      }}
                      onSave={() => {
                        setIsWizardOpen(false);
                        setIsSaveDisabled(false);
                      }}
                    />
                  )}
                  <FormSubmitError error={submitError} />
                  <FormFullWidthLayout>
                    <ActionGroup>
                      <Button
                        aria-label={i18n._(t`Save`)}
                        variant="primary"
                        type="button"
                        onClick={formik.handleSubmit}
                        isDisabled={isSaveDisabled}
                      >
                        {i18n._(t`Save`)}
                      </Button>

                      {isTemplate && showPromptButton && (
                        <Button
                          variant="secondary"
                          type="button"
                          aria-label={i18n._(t`Prompt`)}
                          onClick={() => setIsWizardOpen(true)}
                        >
                          {i18n._(t`Prompt`)}
                        </Button>
                      )}
                      <Button
                        aria-label={i18n._(t`Cancel`)}
                        variant="secondary"
                        type="button"
                        onClick={handleCancel}
                      >
                        {i18n._(t`Cancel`)}
                      </Button>
                    </ActionGroup>
                  </FormFullWidthLayout>
                </FormColumnLayout>
              </Form>
            )}
          </Formik>
        );
      }}
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

export default withI18n()(ScheduleForm);
