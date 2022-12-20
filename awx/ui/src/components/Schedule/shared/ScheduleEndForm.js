import React from 'react';
import { useField } from 'formik';
import { t } from '@lingui/macro';
import { FormGroup, Radio } from '@patternfly/react-core';
import FormField from 'components/FormField';
import DateTimePicker from './DateTimePicker';

function ScheduleEndForm() {
  const [endType, , { setValue }] = useField('endingType');
  const [count] = useField('count');
  return (
    <>
      <FormGroup name="end" label={t`End`}>
        <Radio
          id="endNever"
          name={t`Never End`}
          label={t`Never`}
          value="never"
          isChecked={endType.value === 'never'}
          onChange={() => {
            setValue('never');
          }}
        />
        <Radio
          name="Count"
          id="after"
          label={t`After number of occurrences`}
          value="after"
          isChecked={endType.value === 'after'}
          onChange={() => {
            setValue('after');
          }}
        />
        <Radio
          name="End Date"
          label={t`On date`}
          value="onDate"
          id="endDate"
          isChecked={endType.value === 'onDate'}
          onChange={() => {
            setValue('onDate');
          }}
        />
      </FormGroup>
      {endType.value === 'after' && (
        <FormField
          label={t`Occurrences`}
          name="count"
          type="number"
          min="1"
          step="1"
          isRequired
          {...count}
        />
      )}
      {endType.value === 'onDate' && (
        <DateTimePicker
          dateFieldName="endDate"
          timeFieldName="endTime"
          label={t`End date/time`}
        />
      )}
    </>
  );
}

export default ScheduleEndForm;
