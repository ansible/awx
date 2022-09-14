import React, { useEffect, useCallback, useState } from 'react';
import { shape, func } from 'prop-types';

import { DateTime } from 'luxon';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { RRule } from 'rrule';
import { Button, Form, ActionGroup } from '@patternfly/react-core';
import { Config } from 'contexts/Config';
import { SchedulesAPI } from 'api';
import { dateToInputDateTime } from 'util/dates';
import useRequest from 'hooks/useRequest';
import { parseVariableField } from 'util/yaml';
import ContentError from '../../ContentError';
import ContentLoading from '../../ContentLoading';
import { FormSubmitError } from '../../FormField';
import { FormColumnLayout, FormFullWidthLayout } from '../../FormLayout';
import SchedulePromptableFields from './SchedulePromptableFields';
import ScheduleFormFields from './ScheduleFormFields';
import UnsupportedScheduleForm from './UnsupportedScheduleForm';
import parseRuleObj, { UnsupportedRRuleError } from './parseRuleObj';
import buildRuleObj from './buildRuleObj';
import buildRuleSet from './buildRuleSet';

const NUM_DAYS_PER_FREQUENCY = {
  week: 7,
  month: 31,
  year: 365,
};

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
    result: { zoneOptions, zoneLinks, credentials },
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

      const zones = (data.zones || []).map((zone) => ({
        value: zone,
        key: zone,
        label: zone,
      }));

      return {
        zoneOptions: zones,
        zoneLinks: data.links,
        credentials: creds || [],
      };
    }, [schedule]),
    {
      zonesOptions: [],
      zoneLinks: {},
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
  const initialFrequencyOptions = {
    minute: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
    },
    hour: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
    },
    day: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
    },
    week: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
      daysOfWeek: [],
    },
    month: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
      runOn: 'day',
      runOnTheOccurrence: 1,
      runOnTheDay: 'sunday',
      runOnDayNumber: 1,
    },
    year: {
      interval: 1,
      end: 'never',
      occurrences: 1,
      endDate: tomorrowDate,
      endTime: time,
      runOn: 'day',
      runOnTheOccurrence: 1,
      runOnTheDay: 'sunday',
      runOnTheMonth: 1,
      runOnDayMonth: 1,
      runOnDayNumber: 1,
    },
  };

  const initialValues = {
    description: schedule.description || '',
    frequency: [],
    exceptionFrequency: [],
    frequencyOptions: initialFrequencyOptions,
    exceptionOptions: initialFrequencyOptions,
    name: schedule.name || '',
    startDate: currentDate,
    startTime: time,
    timezone: schedule.timezone || now.zoneName,
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

  let overriddenValues = {};
  if (schedule.rrule) {
    try {
      overriddenValues = parseRuleObj(schedule);
    } catch (error) {
      if (error instanceof UnsupportedRRuleError) {
        return (
          <UnsupportedScheduleForm
            schedule={schedule}
            handleCancel={handleCancel}
          />
        );
      }
      rruleError = error;
    }
  } else if (schedule.id) {
    rruleError = new Error(t`Schedule is missing rrule`);
  }

  if (contentError || rruleError) {
    return <ContentError error={contentError || rruleError} />;
  }

  if (contentLoading) {
    return <ContentLoading />;
  }

  const validate = (values) => {
    const errors = {};

    values.frequency.forEach((freq) => {
      const options = values.frequencyOptions[freq];
      const freqErrors = {};

      if (
        (freq === 'month' || freq === 'year') &&
        options.runOn === 'day' &&
        (options.runOnDayNumber < 1 || options.runOnDayNumber > 31)
      ) {
        freqErrors.runOn = t`Please select a day number between 1 and 31.`;
      }

      if (options.end === 'after' && !options.occurrences) {
        freqErrors.occurrences = t`Please enter a number of occurrences.`;
      }

      if (options.end === 'onDate') {
        if (
          DateTime.fromISO(values.startDate) >=
          DateTime.fromISO(options.endDate)
        ) {
          freqErrors.endDate = t`Please select an end date/time that comes after the start date/time.`;
        }

        if (
          DateTime.fromISO(options.endDate)
            .diff(DateTime.fromISO(values.startDate), 'days')
            .toObject().days < NUM_DAYS_PER_FREQUENCY[freq]
        ) {
          const rule = new RRule(
            buildRuleObj({
              startDate: values.startDate,
              startTime: values.startTime,
              frequency: freq,
              ...options,
            })
          );
          if (rule.all().length === 0) {
            errors.startDate = t`Selected date range must have at least 1 schedule occurrence.`;
            freqErrors.endDate = t`Selected date range must have at least 1 schedule occurrence.`;
          }
        }
      }
      if (Object.keys(freqErrors).length > 0) {
        if (!errors.frequencyOptions) {
          errors.frequencyOptions = {};
        }
        errors.frequencyOptions[freq] = freqErrors;
      }
    });

    if (values.exceptionFrequency.length > 0 && !scheduleHasInstances(values)) {
      errors.exceptionFrequency = t`This schedule has no occurrences due to the selected exceptions.`;
    }

    return errors;
  };

  return (
    <Config>
      {() => (
        <Formik
          initialValues={{
            ...initialValues,
            ...overriddenValues,
            frequencyOptions: {
              ...initialValues.frequencyOptions,
              ...overriddenValues.frequencyOptions,
            },
            exceptionOptions: {
              ...initialValues.exceptionOptions,
              ...overriddenValues.exceptionOptions,
            },
          }}
          onSubmit={(values) => {
            submitSchedule(values, launchConfig, surveyConfig, credentials);
          }}
          validate={validate}
        >
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <ScheduleFormFields
                  hasDaysToKeepField={hasDaysToKeepField}
                  zoneOptions={zoneOptions}
                  zoneLinks={zoneLinks}
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

function scheduleHasInstances(values) {
  let rangeToCheck = 1;
  values.frequency.forEach((freq) => {
    if (NUM_DAYS_PER_FREQUENCY[freq] > rangeToCheck) {
      rangeToCheck = NUM_DAYS_PER_FREQUENCY[freq];
    }
  });

  const ruleSet = buildRuleSet(values, true);
  const startDate = DateTime.fromISO(values.startDate);
  const endDate = startDate.plus({ days: rangeToCheck });
  const instances = ruleSet.between(
    startDate.toJSDate(),
    endDate.toJSDate(),
    true,
    (date, i) => i === 0
  );

  return instances.length > 0;
}
