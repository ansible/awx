import React, { useEffect, useCallback } from 'react';
import { shape, func } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { Config } from '@contexts/Config';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import { SchedulesAPI } from '@api';
import AnsibleSelect from '@components/AnsibleSelect';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from '@components/FormField';
import { FormColumnLayout, SubFormLayout } from '@components/FormLayout';
import { dateToInputDateTime } from '@util/dates';
import useRequest from '@util/useRequest';
import { required } from '@util/validators';
import FrequencyDetailSubform from './FrequencyDetailSubform';

function ScheduleFormFields({ i18n, zoneOptions }) {
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
        isValid={!startDateTimeMeta.touched || !startDateTimeMeta.error}
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
        isValid={!timezoneMeta.touched || !timezoneMeta.error}
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
        isValid={!frequencyMeta.touched || !frequencyMeta.error}
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
      {frequency.value !== 'none' && (
        <SubFormLayout>
          <Title size="md">{i18n._(t`Frequency Details`)}</Title>
          <FormColumnLayout>
            <FrequencyDetailSubform />
          </FormColumnLayout>
        </SubFormLayout>
      )}
    </>
  );
}

function ScheduleForm({
  handleCancel,
  handleSubmit,
  i18n,
  schedule,
  submitError,
  ...rest
}) {
  const now = new Date();
  const closestQuarterHour = new Date(
    Math.ceil(now.getTime() / 900000) * 900000
  );
  const tomorrow = new Date(closestQuarterHour);
  tomorrow.setDate(tomorrow.getDate() + 1);

  const {
    request: loadZoneInfo,
    error: contentError,
    contentLoading,
    result: zoneOptions,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SchedulesAPI.readZoneInfo();
      return data.map(zone => {
        return {
          value: zone.name,
          key: zone.name,
          label: zone.name,
        };
      });
    }, [])
  );

  useEffect(() => {
    loadZoneInfo();
  }, [loadZoneInfo]);

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (contentLoading) {
    return <ContentLoading />;
  }

  return (
    <Config>
      {() => {
        return (
          <Formik
            initialValues={{
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
            }}
            onSubmit={handleSubmit}
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
                  t`Please select a day number between 1 and 31`
                );
              }

              return errors;
            }}
          >
            {formik => (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
                  <ScheduleFormFields
                    i18n={i18n}
                    zoneOptions={zoneOptions}
                    {...rest}
                  />
                  <FormSubmitError error={submitError} />
                  <FormActionGroup
                    onCancel={handleCancel}
                    onSubmit={formik.handleSubmit}
                  />
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
