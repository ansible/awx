import React, { useState } from 'react';
import { useField } from 'formik';
import { FormGroup } from '@patternfly/react-core';
import { t } from '@lingui/macro';
import FormField from 'components/FormField';
import { required } from 'util/validators';
import { useConfig } from 'contexts/Config';
import Popover from '../../Popover';
import AnsibleSelect from '../../AnsibleSelect';
import getHelpText from '../../../screens/Template/shared/JobTemplate.helptext';
import DateTimePicker from './DateTimePicker';

export default function ScheduleFormFields({
  hasDaysToKeepField,
  zoneOptions,
  zoneLinks,
  setTimeZone,
}) {
  const helpText = getHelpText();
  const [timezone, timezoneMeta] = useField({
    name: 'timezone',
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
    setTimeZone(zoneLinks(selectedValue));
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
    </>
  );
}
