import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  DatePicker,
  isValidDate,
  yyyyMMddFormat,
  TimePicker,
  FormGroup,
} from '@patternfly/react-core';
import styled from 'styled-components';
import { required, validateTime, combine } from 'util/validators';

const DateTimeGroup = styled.span`
  display: flex;
`;
function DateTimePicker({ dateFieldName, timeFieldName, label }) {
  const [dateField, dateMeta, dateHelpers] = useField({
    name: `${dateFieldName}`,
    validate: combine([required(null), isValidDate]),
  });
  const [timeField, timeMeta, timeHelpers] = useField({
    name: `${timeFieldName}`,
    validate: combine([required(null), validateTime()]),
  });

  const onDateChange = (inputDate, newDate) => {
    dateHelpers.setTouched();
    if (isValidDate(newDate) && inputDate === yyyyMMddFormat(newDate)) {
      dateHelpers.setValue(new Date(newDate).toISOString().split('T')[0]);
    }
  };

  return (
    <FormGroup
      fieldId={`schedule-${label}-datetime`}
      helperTextInvalid={dateMeta.error || timeMeta.error}
      isRequired
      validated={
        (!dateMeta.touched || !dateMeta.error) &&
        (!timeMeta.touched || !timeMeta.error)
          ? 'default'
          : 'error'
      }
      label={`${label} date/time`}
    >
      <DateTimeGroup>
        <DatePicker
          aria-label={t`${label} date`}
          {...dateField}
          value={dateField.value.split('T')[0]}
          onChange={onDateChange}
        />
        <TimePicker
          placeholder="hh:mm AM/PM"
          stepMinutes={15}
          aria-label={t`${label} time`}
          time={timeField.value}
          {...timeField}
          onChange={(time) => timeHelpers.setValue(time)}
        />
      </DateTimeGroup>
    </FormGroup>
  );
}

export default DateTimePicker;
