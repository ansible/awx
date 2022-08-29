import React, { useState } from 'react';
import { useField } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import 'styled-components/macro';
import FormField from 'components/FormField';
import { required } from 'util/validators';
import { useConfig } from 'contexts/Config';
import Popover from '../../Popover';
import AnsibleSelect from '../../AnsibleSelect';
import FrequencySelect, { SelectOption } from './FrequencySelect';
import helpText from '../../../screens/Template/shared/JobTemplate.helptext';
import { SubFormLayout, FormColumnLayout } from '../../FormLayout';
import FrequencyDetailSubform from './FrequencyDetailSubform';
import DateTimePicker from './DateTimePicker';
import sortFrequencies from './sortFrequencies';

const SelectClearOption = styled(SelectOption)`
  & > input[type='checkbox'] {
    display: none;
  }
`;

export default function ScheduleFormFields({
  hasDaysToKeepField,
  zoneOptions,
  zoneLinks,
}) {
  const [timezone, timezoneMeta] = useField({
    name: 'timezone',
    validate: required(t`Select a value for this field`),
  });
  const [frequency, frequencyMeta, frequencyHelper] = useField({
    name: 'frequency',
    validate: required(t`Select a value for this field`),
  });
  const [timezoneMessage, setTimezoneMessage] = useState('');
  const warnLinkedTZ = (event, selectedValue) => {
    if (zoneLinks[selectedValue]) {
      setTimezoneMessage(
        t`Warning: ${selectedValue} is a link to ${zoneLinks[selectedValue]} and will be saved as that.`
      );
    } else {
      setTimezoneMessage('');
    }
    timezone.onChange(event, selectedValue);
  };
  let timezoneValidatedStatus = 'default';
  if (timezoneMeta.touched && timezoneMeta.error) {
    timezoneValidatedStatus = 'error';
  } else if (timezoneMessage) {
    timezoneValidatedStatus = 'warning';
  }
  const config = useConfig();

  const [exceptionFrequency, exceptionFrequencyMeta, exceptionFrequencyHelper] =
    useField({
      name: 'exceptionFrequency',
      validate: required(t`Select a value for this field`),
    });

  const updateFrequency = (setFrequency) => (values) => {
    setFrequency(values.sort(sortFrequencies));
  };

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
        dateFieldName="startDate"
        timeFieldName="startTime"
        label={t`Start date/time`}
      />
      <FormGroup
        name="timezone"
        fieldId="schedule-timezone"
        helperTextInvalid={timezoneMeta.error || timezoneMessage}
        isRequired
        validated={timezoneValidatedStatus}
        label={t`Local time zone`}
        helperText={timezoneMessage}
        labelIcon={<Popover content={helpText.localTimeZone(config)} />}
      >
        <AnsibleSelect
          id="schedule-timezone"
          data={zoneOptions}
          {...timezone}
          onChange={warnLinkedTZ}
        />
      </FormGroup>
      <FormGroup
        name="frequency"
        fieldId="schedule-frequency"
        helperTextInvalid={frequencyMeta.error}
        validated={
          !frequencyMeta.touched || !frequencyMeta.error ? 'default' : 'error'
        }
        label={t`Repeat frequency`}
      >
        <FrequencySelect
          id="schedule-frequency"
          onChange={updateFrequency(frequencyHelper.setValue)}
          value={frequency.value}
          placeholderText={
            frequency.value.length ? t`Select frequency` : t`None (run once)`
          }
          onBlur={frequencyHelper.setTouched}
        >
          <SelectClearOption value="none">{t`None (run once)`}</SelectClearOption>
          <SelectOption value="minute">{t`Minute`}</SelectOption>
          <SelectOption value="hour">{t`Hour`}</SelectOption>
          <SelectOption value="day">{t`Day`}</SelectOption>
          <SelectOption value="week">{t`Week`}</SelectOption>
          <SelectOption value="month">{t`Month`}</SelectOption>
          <SelectOption value="year">{t`Year`}</SelectOption>
        </FrequencySelect>
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
      {frequency.value.length ? (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {t`Frequency Details`}
          </Title>
          {frequency.value.map((val) => (
            <FormColumnLayout key={val} stacked>
              <FrequencyDetailSubform
                frequency={val}
                prefix={`frequencyOptions.${val}`}
              />
            </FormColumnLayout>
          ))}
          <Title
            size="md"
            headingLevel="h4"
            css="margin-top: var(--pf-c-card--child--PaddingRight)"
          >{t`Exceptions`}</Title>
          <FormColumnLayout stacked>
            <FormGroup
              name="exceptions"
              fieldId="exception-frequency"
              helperTextInvalid={exceptionFrequencyMeta.error}
              validated={
                !exceptionFrequencyMeta.touched || !exceptionFrequencyMeta.error
                  ? 'default'
                  : 'error'
              }
              label={t`Add exceptions`}
            >
              <FrequencySelect
                id="exception-frequency"
                onChange={exceptionFrequencyHelper.setValue}
                value={exceptionFrequency.value}
                placeholderText={t`None`}
                onBlur={exceptionFrequencyHelper.setTouched}
              >
                <SelectClearOption value="none">{t`None`}</SelectClearOption>
                <SelectOption value="minute">{t`Minute`}</SelectOption>
                <SelectOption value="hour">{t`Hour`}</SelectOption>
                <SelectOption value="day">{t`Day`}</SelectOption>
                <SelectOption value="week">{t`Week`}</SelectOption>
                <SelectOption value="month">{t`Month`}</SelectOption>
                <SelectOption value="year">{t`Year`}</SelectOption>
              </FrequencySelect>
            </FormGroup>
          </FormColumnLayout>
          {exceptionFrequency.value.map((val) => (
            <FormColumnLayout key={val} stacked>
              <FrequencyDetailSubform
                frequency={val}
                prefix={`exceptionOptions.${val}`}
                isException
              />
            </FormColumnLayout>
          ))}
        </SubFormLayout>
      ) : null}
    </>
  );
}
