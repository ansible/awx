import React, { useState } from 'react';
import { useField } from 'formik';
import { FormGroup, Title } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { required } from 'util/validators';
import { useConfig } from 'contexts/Config';
import Popover from '../../Popover';
import AnsibleSelect from '../../AnsibleSelect';
import FormField, {
  Select,
  SelectOption,
  SelectVariant,
} from '../../FormField';
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
        fieldId="schedule-requency"
        helperTextInvalid={frequencyMeta.error}
        isRequired
        validated={
          !frequencyMeta.touched || !frequencyMeta.error ? 'default' : 'error'
        }
        label={t`Repeat frequency`}
      >
        <Select
          variant={SelectVariant.checkbox}
          onChange={frequencyHelper.setValue}
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
        </Select>
        {/* <Select
          variant={SelectVariant.checkbox}
          onSelect={(a, b) => console.log({ a, b })}
          selections={[]}
          placeholderText={t`Select frequency`}
          onToggle={(val) => setIsOpen(val)}
          isOpen={isOpen}
        >
          <SelectOption value="none">{t`None (run once)`}</SelectOption>
          <SelectOption value="minute">{t`Minute`}</SelectOption>
          <SelectOption value="hour">{t`Hour`}</SelectOption>
          <SelectOption value="day">{t`Day`}</SelectOption>
          <SelectOption value="week">{t`Week`}</SelectOption>
          <SelectOption value="month">{t`Month`}</SelectOption>
          <SelectOption value="year">{t`Year`}</SelectOption>
        </Select>
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
        /> */}
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
              <FrequencyDetailSubform frequency={val} />
            </FormColumnLayout>
          ))}
        </SubFormLayout>
      ) : null}
    </>
  );
}
