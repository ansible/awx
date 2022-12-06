import { Trans } from '@lingui/macro';
import { FormGroup, TextInput } from '@patternfly/react-core';
import AnsibleSelect from 'components/AnsibleSelect';
import { useField } from 'formik';
import React from 'react';
import styled from 'styled-components';

const RunOnRadio = styled(Radio)`
  display: flex;
  align-items: center;

  label {
    display: block;
    width: 100%;
  }

  :not(:last-of-type) {
    margin-bottom: 10px;
  }

  select:not(:first-of-type) {
    margin-left: 10px;
  }
`;

function MonthYearSubForm({ prefix, id, frequency }) {
  const [runOn, runOnMeta] = useField({
    name: `${prefix}.runOn`,
    validate: (val) => {
      if (frequency === 'month' || frequency === 'year') {
        return required(t`Select a value for this field`)(val);
      }
      return undefined;
    },
  });
  return (
    !Number.isNaN(new Date(startDate.value)) && (
      <FormGroup
        name={`${prefix}.runOn`}
        fieldId={`schedule-run-on-${id}`}
        helperTextInvalid={runOnMeta.error}
        isRequired
        validated={!runOnMeta.touched || !runOnMeta.error ? 'default' : 'error'}
        label={t`Run on`}
      >
        <RunOnRadio
          id={`schedule-run-on-day-${id}`}
          name={`${prefix}.runOn`}
          label={
            <div css="display: flex;align-items: center;">
              {frequency === 'month' && (
                <span id="radio-schedule-run-on-day" css="margin-right: 10px;">
                  <Trans>Day</Trans>
                </span>
              )}
              {frequency === 'year' && (
                <AnsibleSelect
                  id={`schedule-run-on-day-month-${id}`}
                  css="margin-right: 10px"
                  isDisabled={runOn.value !== 'day'}
                  data={monthOptions}
                  {...runOnDayMonth}
                />
              )}
              <TextInput
                id={`schedule-run-on-day-number-${id}`}
                type="number"
                min="1"
                max="31"
                step="1"
                isDisabled={runOn.value !== 'day'}
                {...runOnDayNumber}
                onChange={(value, event) => {
                  runOnDayNumber.onChange(event);
                }}
              />
            </div>
          }
          value="day"
          isChecked={runOn.value === 'day'}
          onChange={(value, event) => {
            event.target.value = 'day';
            runOn.onChange(event);
          }}
        />
        <RunOnRadio
          id={`schedule-run-on-the-${id}`}
          name={`${prefix}.runOn`}
          label={
            <div css="display: flex;align-items: center;">
              <span
                id={`radio-schedule-run-on-the-${id}`}
                css="margin-right: 10px;"
              >
                <Trans>The</Trans>
              </span>
              <AnsibleSelect
                id={`schedule-run-on-the-occurrence-${id}`}
                isDisabled={runOn.value !== 'the'}
                data={[
                  { value: 1, key: 'first', label: t`First` },
                  {
                    value: 2,
                    key: 'second',
                    label: t`Second`,
                  },
                  { value: 3, key: 'third', label: t`Third` },
                  {
                    value: 4,
                    key: 'fourth',
                    label: t`Fourth`,
                  },
                  { value: 5, key: 'fifth', label: t`Fifth` },
                  { value: -1, key: 'last', label: t`Last` },
                ]}
                {...runOnTheOccurrence}
              />
              <AnsibleSelect
                id={`schedule-run-on-the-day-${id}`}
                isDisabled={runOn.value !== 'the'}
                data={[
                  {
                    value: 'sunday',
                    key: 'sunday',
                    label: t`Sunday`,
                  },
                  {
                    value: 'monday',
                    key: 'monday',
                    label: t`Monday`,
                  },
                  {
                    value: 'tuesday',
                    key: 'tuesday',
                    label: t`Tuesday`,
                  },
                  {
                    value: 'wednesday',
                    key: 'wednesday',
                    label: t`Wednesday`,
                  },
                  {
                    value: 'thursday',
                    key: 'thursday',
                    label: t`Thursday`,
                  },
                  {
                    value: 'friday',
                    key: 'friday',
                    label: t`Friday`,
                  },
                  {
                    value: 'saturday',
                    key: 'saturday',
                    label: t`Saturday`,
                  },
                  { value: 'day', key: 'day', label: t`Day` },
                  {
                    value: 'weekday',
                    key: 'weekday',
                    label: t`Weekday`,
                  },
                  {
                    value: 'weekendDay',
                    key: 'weekendDay',
                    label: t`Weekend day`,
                  },
                ]}
                {...runOnTheDay}
              />
              {frequency === 'year' && (
                <>
                  <span
                    id={`of-schedule-run-on-the-month-${id}`}
                    css="margin-left: 10px;"
                  >
                    <Trans>of</Trans>
                  </span>
                  <AnsibleSelect
                    id={`schedule-run-on-the-month-${id}`}
                    isDisabled={runOn.value !== 'the'}
                    data={monthOptions}
                    {...runOnTheMonth}
                  />
                </>
              )}
            </div>
          }
          value="the"
          isChecked={runOn.value === 'the'}
          onChange={(value, event) => {
            event.target.value = 'the';
            runOn.onChange(event);
          }}
        />
      </FormGroup>
    )
  );
}
export default MonthYearSubForm;
