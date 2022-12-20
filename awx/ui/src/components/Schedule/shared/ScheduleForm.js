import React, { useEffect, useCallback, useState, useRef } from 'react';
import { shape, func } from 'prop-types';
import { DateTime } from 'luxon';
import { t } from '@lingui/macro';
import { Formik } from 'formik';
import { RRule } from 'rrule';
import { Button, Form, ActionGroup } from '@patternfly/react-core';
import { Config } from 'contexts/Config';
import { JobTemplatesAPI, SchedulesAPI, WorkflowJobTemplatesAPI } from 'api';
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
import ScheduleFormWizard from './ScheduleFormWizard';
import FrequenciesList from './FrequenciesList';
// import { validateSchedule } from './scheduleFormHelpers';

function ScheduleForm({
  hasDaysToKeepField,
  handleCancel,
  handleSubmit: submitSchedule,
  schedule,
  submitError,
  resource,
  launchConfig,
  surveyConfig,
  resourceDefaultCredentials,
}) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const [isSaveDisabled, setIsSaveDisabled] = useState(false);
  const [isScheduleWizardOpen, setIsScheduleWizardOpen] = useState(false);
  const originalLabels = useRef([]);
  const originalInstanceGroups = useRef([]);

  let rruleError;
  const now = DateTime.now();

  const closestQuarterHour = DateTime.fromMillis(
    Math.ceil(now.ts / 900000) * 900000
  );
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

      let creds = [];
      let allLabels = [];
      let allInstanceGroups = [];
      if (schedule.id) {
        if (
          resource.type === 'job_template' &&
          launchConfig?.ask_credential_on_launch
        ) {
          const {
            data: { results },
          } = await SchedulesAPI.readCredentials(schedule.id);
          creds = results;
        }
        if (launchConfig?.ask_labels_on_launch) {
          const {
            data: { results },
          } = await SchedulesAPI.readAllLabels(schedule.id);
          allLabels = results;
        }
        if (
          resource.type === 'job_template' &&
          launchConfig?.ask_instance_groups_on_launch
        ) {
          const {
            data: { results },
          } = await SchedulesAPI.readInstanceGroups(schedule.id);
          allInstanceGroups = results;
        }
      } else {
        if (resource.type === 'job_template') {
          if (launchConfig?.ask_labels_on_launch) {
            const {
              data: { results },
            } = await JobTemplatesAPI.readAllLabels(resource.id);
            allLabels = results;
          }
        }
        if (
          resource.type === 'workflow_job_template' &&
          launchConfig?.ask_labels_on_launch
        ) {
          const {
            data: { results },
          } = await WorkflowJobTemplatesAPI.readAllLabels(resource.id);
          allLabels = results;
        }
      }

      const zones = (data.zones || []).map((zone) => ({
        value: zone,
        key: zone,
        label: zone,
      }));

      originalLabels.current = allLabels;
      originalInstanceGroups.current = allInstanceGroups;

      return {
        zoneOptions: zones,
        zoneLinks: data.links,
        credentials: creds,
      };
    }, [schedule, resource.id, resource.type, launchConfig]),
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
      launchConfig?.inventory_needed_to_start &&
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
      launchConfig.ask_execution_environment_on_launch ||
      launchConfig.ask_labels_on_launch ||
      launchConfig.ask_forks_on_launch ||
      launchConfig.ask_job_slice_count_on_launch ||
      launchConfig.ask_timeout_on_launch ||
      launchConfig.ask_instance_groups_on_launch ||
      launchConfig.survey_enabled ||
      launchConfig.inventory_needed_to_start ||
      launchConfig.variables_needed_to_start?.length > 0)
  ) {
    showPromptButton = true;
  }
  const [currentDate, time] = dateToInputDateTime(closestQuarterHour.toISO());

  const initialValues = {
    description: schedule.description || '',
    frequencies: [],
    exceptionFrequency: [],
    name: schedule.name || '',
    startDate: currentDate,
    startTime: time,
    timezone: schedule.timezone || now.zoneName,
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
  if (schedule.rrule) {
    try {
      parseRuleObj(schedule);
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
  const frequencies = [];
  frequencies.push(parseRuleObj(schedule));
  return (
    <Config>
      {() => (
        <Formik
          initialValues={{
            name: schedule.name || '',
            description: schedule.description || '',
            frequencies: frequencies || [],
            freq: RRule.DAILY,
            interval: 1,
            wkst: RRule.SU,
            byweekday: [],
            byweekno: [],
            bymonth: [],
            bymonthday: '',
            byyearday: '',
            bysetpos: '',
            until: schedule.until || null,
            endDate: currentDate,
            endTime: time,
            count: 1,
            endingType: 'never',
            timezone: schedule.timezone || now.zoneName,
            startDate: currentDate,
            startTime: time,
          }}
          onSubmit={(values) => {
            submitSchedule(
              values,
              launchConfig,
              surveyConfig,
              originalInstanceGroups.current,
              originalLabels.current,
              credentials
            );
          }}
          validate={() => {}}
        >
          {(formik) => (
            <>
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
                      labels={originalLabels.current}
                      instanceGroups={originalInstanceGroups.current}
                    />
                  )}
                  <FormFullWidthLayout>
                    <FrequenciesList openWizard={setIsScheduleWizardOpen} />
                  </FormFullWidthLayout>
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

                      <Button
                        onClick={() => {}}
                      >{t`Preview occurances`}</Button>

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
              {isScheduleWizardOpen && (
                <ScheduleFormWizard
                  staticFormFormkik={formik}
                  isOpen={isScheduleWizardOpen}
                  handleSave={() => {}}
                  setIsOpen={setIsScheduleWizardOpen}
                />
              )}
            </>
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
