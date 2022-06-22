import React, { useState } from 'react';
import { useField, useFormikContext } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import FormField from 'components/FormField';
import { required } from 'util/validators';
import { useConfig } from 'contexts/Config';
import Popover from '../../Popover';
import AnsibleSelect from '../../AnsibleSelect';
import FrequencySelect, {
  SelectOption,
  SelectVariant,
} from './FrequencySelect';
import helpText from '../../../screens/Template/shared/JobTemplate.helptext';
import { SubFormLayout, FormColumnLayout } from '../../FormLayout';
import FrequencyDetailSubform from './FrequencyDetailSubform';
import DateTimePicker from './DateTimePicker';

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
  const { values, setFieldValue } = useFormikContext();
  const [timezone, timezoneMeta] = useField({
    name: 'timezone',
    validate: required(t`Select a value for this field`),
  });
  const [frequency, frequencyMeta, frequencyHelper] = useField({
    name: 'frequency',
    validate: required(t`Select a value for this field`),
  });
  // const [exemptFrequency, exemptFrequencyMeta, exemptFrequencyHelper] =
  //   useField({
  //     name: 'exempt_frequency',
  //     validate: required(t`Select a value for this field`),
  //   });
  const [{ name: dateFieldName }] = useField('startDate');
  const [{ name: timeFieldName }] = useField('startTime');
  const [timezoneMessage, setTimezoneMessage] = useState('');
  const warnLinkedTZ = (event, selectedValue) => {
    if (zoneLinks[selectedValue]) {
      setTimezoneMessage(
        `Warning: ${selectedValue} is a link to ${zoneLinks[selectedValue]} and will be saved as that.`
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

  const initField = (fieldName, value) => {
    if (typeof values[fieldName] === 'undefined') {
      setFieldValue(fieldName, value, false);
    }
  };

  const initFrequencyFields = (prefix, freq) => {
    initField(`${prefix}_${freq}_end`, 'never');
    // initField(`${prefix}_${freq}_endTime`, '');
    initField(`${prefix}_${freq}_interval`, 1);
    initField(`${prefix}_${freq}_occurences`, 1);
    initField(`${prefix}_${freq}_runOnDayMonth`, 1);
    initField(`${prefix}_${freq}_runOnDayNumber`, 1);
    initField(`${prefix}_${freq}_runOnTheDay`, 'sunday');
    initField(`${prefix}_${freq}_runOnTheMonth`, 1);
    initField(`${prefix}_${freq}_runOnTheOccurence`, 1);
    initField(`${prefix}_${freq}_daysOfWeek`, []);
    initField(`${prefix}_${freq}_runOn`, 'day');
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
          variant={SelectVariant.checkbox}
          onChange={(newFrequency) => {
            initFrequencyFields('frequency', newFrequency);
            if (
              typeof values[`frequency_${newFrequency}_end`] === 'undefined'
            ) {
              setFieldValue(`frequency_${newFrequency}_end`, '');
            }
            frequencyHelper.setValue(newFrequency);
          }}
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
          {/* TODO: sort into predictable/logical order */}
          {frequency.value.map((val) => (
            <FormColumnLayout key={val} stacked>
              <FrequencyDetailSubform
                frequency={val}
                prefix={`frequency_${val}`}
              />
            </FormColumnLayout>
          ))}
          <Title size="md" headingLevel="h4">{t`Exceptions`}</Title>
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
              variant={SelectVariant.checkbox}
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
          {exceptionFrequency.value.map((val) => (
            <FormColumnLayout key={val} stacked>
              <FrequencyDetailSubform
                frequency={val}
                prefix={`exception_${val}`}
              />
            </FormColumnLayout>
          ))}
        </SubFormLayout>
      ) : null}
    </>
  );
}
