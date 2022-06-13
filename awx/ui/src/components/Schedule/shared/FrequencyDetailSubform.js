import 'styled-components/macro';
import React from 'react';
import styled from 'styled-components';
import { useField } from 'formik';

import { t, Trans, Plural } from '@lingui/macro';
import { RRule } from 'rrule';
import {
  Checkbox as _Checkbox,
  FormGroup,
  Radio,
  TextInput,
} from '@patternfly/react-core';
import { required } from 'util/validators';
import AnsibleSelect from '../../AnsibleSelect';
import FormField from '../../FormField';
import DateTimePicker from './DateTimePicker';

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

const RunEveryLabel = styled.p`
  display: flex;
  align-items: center;
`;

const Checkbox = styled(_Checkbox)`
  :not(:last-of-type) {
    margin-right: 10px;
  }
`;

export function requiredPositiveInteger() {
  return (value) => {
    if (typeof value === 'number') {
      if (!Number.isInteger(value)) {
        return t`This field must be an integer`;
      }
      if (value < 1) {
        return t`This field must be greater than 0`;
      }
    }
    if (!value) {
      return t`Select a value for this field`;
    }
    return undefined;
  };
}

const FrequencyDetailSubform = () => {
  const [runOnDayMonth] = useField({
    name: 'runOnDayMonth',
  });
  const [runOnDayNumber] = useField({
    name: 'runOnDayNumber',
  });
  const [runOnTheOccurrence] = useField({
    name: 'runOnTheOccurrence',
  });
  const [runOnTheDay] = useField({
    name: 'runOnTheDay',
  });
  const [runOnTheMonth] = useField({
    name: 'runOnTheMonth',
  });
  const [startDate] = useField('startDate');
  const [{ name: dateFieldName }] = useField('endDate');
  const [{ name: timeFieldName }] = useField('endTime');

  const [daysOfWeek, daysOfWeekMeta, daysOfWeekHelpers] = useField({
    name: 'daysOfWeek',
    validate: required(t`Select a value for this field`),
  });
  const [end, endMeta] = useField({
    name: 'end',
    validate: required(t`Select a value for this field`),
  });
  const [interval, intervalMeta] = useField({
    name: 'interval',
    validate: requiredPositiveInteger(),
  });
  const [runOn, runOnMeta] = useField({
    name: 'runOn',
    validate: required(t`Select a value for this field`),
  });
  const [frequency] = useField({
    name: 'frequency',
  });
  useField({
    name: 'occurrences',
    validate: requiredPositiveInteger(),
  });

  const monthOptions = [
    {
      key: 'january',
      value: 1,
      label: t`January`,
    },
    {
      key: 'february',
      value: 2,
      label: t`February`,
    },
    {
      key: 'march',
      value: 3,
      label: t`March`,
    },
    {
      key: 'april',
      value: 4,
      label: t`April`,
    },
    {
      key: 'may',
      value: 5,
      label: t`May`,
    },
    {
      key: 'june',
      value: 6,
      label: t`June`,
    },
    {
      key: 'july',
      value: 7,
      label: t`July`,
    },
    {
      key: 'august',
      value: 8,
      label: t`August`,
    },
    {
      key: 'september',
      value: 9,
      label: t`September`,
    },
    {
      key: 'october',
      value: 10,
      label: t`October`,
    },
    {
      key: 'november',
      value: 11,
      label: t`November`,
    },
    {
      key: 'december',
      value: 12,
      label: t`December`,
    },
  ];

  const updateDaysOfWeek = (day, checked) => {
    const newDaysOfWeek = [...daysOfWeek.value];
    if (checked) {
      newDaysOfWeek.push(day);
      daysOfWeekHelpers.setValue(newDaysOfWeek);
    } else {
      daysOfWeekHelpers.setValue(
        newDaysOfWeek.filter((selectedDay) => selectedDay !== day)
      );
    }
  };

  const getRunEveryLabel = () => {
    const intervalValue = interval.value;

    switch (frequency.value) {
      case 'minute':
        return <Plural value={intervalValue} one="minute" other="minutes" />;
      case 'hour':
        return <Plural value={intervalValue} one="hour" other="hours" />;
      case 'day':
        return <Plural value={intervalValue} one="day" other="days" />;
      case 'week':
        return <Plural value={intervalValue} one="week" other="weeks" />;
      case 'month':
        return <Plural value={intervalValue} one="month" other="months" />;
      case 'year':
        return <Plural value={intervalValue} one="year" other="years" />;
      default:
        throw new Error(t`Frequency did not match an expected value`);
    }
  };

  /* eslint-disable no-restricted-globals */
  return (
    <>
      <FormGroup
        name="interval"
        fieldId="schedule-run-every"
        helperTextInvalid={intervalMeta.error}
        isRequired
        validated={
          !intervalMeta.touched || !intervalMeta.error ? 'default' : 'error'
        }
        label={t`Run every`}
      >
        <div css="display: flex">
          <TextInput
            css="margin-right: 10px;"
            id="schedule-run-every"
            type="number"
            min="1"
            step="1"
            {...interval}
            onChange={(value, event) => {
              interval.onChange(event);
            }}
          />
          <RunEveryLabel>{getRunEveryLabel()}</RunEveryLabel>
        </div>
      </FormGroup>
      {frequency?.value === 'week' && (
        <FormGroup
          name="daysOfWeek"
          fieldId="schedule-days-of-week"
          helperTextInvalid={daysOfWeekMeta.error}
          isRequired
          validated={
            !daysOfWeekMeta.touched || !daysOfWeekMeta.error
              ? 'default'
              : 'error'
          }
          label={t`On days`}
        >
          <div css="display: flex">
            <Checkbox
              label={t`Sun`}
              isChecked={daysOfWeek.value.includes(RRule.SU)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.SU, checked);
              }}
              aria-label={t`Sunday`}
              id="schedule-days-of-week-sun"
              ouiaId="schedule-days-of-week-sun"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Mon`}
              isChecked={daysOfWeek.value.includes(RRule.MO)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.MO, checked);
              }}
              aria-label={t`Monday`}
              id="schedule-days-of-week-mon"
              ouiaId="schedule-days-of-week-mon"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Tue`}
              isChecked={daysOfWeek.value.includes(RRule.TU)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.TU, checked);
              }}
              aria-label={t`Tuesday`}
              id="schedule-days-of-week-tue"
              ouiaId="schedule-days-of-week-tue"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Wed`}
              isChecked={daysOfWeek.value.includes(RRule.WE)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.WE, checked);
              }}
              aria-label={t`Wednesday`}
              id="schedule-days-of-week-wed"
              ouiaId="schedule-days-of-week-wed"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Thu`}
              isChecked={daysOfWeek.value.includes(RRule.TH)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.TH, checked);
              }}
              aria-label={t`Thursday`}
              id="schedule-days-of-week-thu"
              ouiaId="schedule-days-of-week-thu"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Fri`}
              isChecked={daysOfWeek.value.includes(RRule.FR)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.FR, checked);
              }}
              aria-label={t`Friday`}
              id="schedule-days-of-week-fri"
              ouiaId="schedule-days-of-week-fri"
              name="daysOfWeek"
            />
            <Checkbox
              label={t`Sat`}
              isChecked={daysOfWeek.value.includes(RRule.SA)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.SA, checked);
              }}
              aria-label={t`Saturday`}
              id="schedule-days-of-week-sat"
              ouiaId="schedule-days-of-week-sat"
              name="daysOfWeek"
            />
          </div>
        </FormGroup>
      )}
      {(frequency?.value === 'month' || frequency?.value === 'year') &&
        !isNaN(new Date(startDate.value)) && (
          <FormGroup
            name="runOn"
            fieldId="schedule-run-on"
            helperTextInvalid={runOnMeta.error}
            isRequired
            validated={
              !runOnMeta.touched || !runOnMeta.error ? 'default' : 'error'
            }
            label={t`Run on`}
          >
            <RunOnRadio
              id="schedule-run-on-day"
              name="runOn"
              label={
                <div css="display: flex;align-items: center;">
                  {frequency?.value === 'month' && (
                    <span
                      id="radio-schedule-run-on-day"
                      css="margin-right: 10px;"
                    >
                      <Trans>Day</Trans>
                    </span>
                  )}
                  {frequency?.value === 'year' && (
                    <AnsibleSelect
                      id="schedule-run-on-day-month"
                      css="margin-right: 10px"
                      isDisabled={runOn.value !== 'day'}
                      data={monthOptions}
                      {...runOnDayMonth}
                    />
                  )}
                  <TextInput
                    id="schedule-run-on-day-number"
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
              id="schedule-run-on-the"
              name="runOn"
              label={
                <div css="display: flex;align-items: center;">
                  <span
                    id="radio-schedule-run-on-the"
                    css="margin-right: 10px;"
                  >
                    <Trans>The</Trans>
                  </span>
                  <AnsibleSelect
                    id="schedule-run-on-the-occurrence"
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
                    id="schedule-run-on-the-day"
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
                  {frequency?.value === 'year' && (
                    <>
                      <span
                        id="of-schedule-run-on-the-month"
                        css="margin-left: 10px;"
                      >
                        <Trans>of</Trans>
                      </span>
                      <AnsibleSelect
                        id="schedule-run-on-the-month"
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
        )}
      <FormGroup
        name="end"
        fieldId="schedule-end"
        helperTextInvalid={endMeta.error}
        isRequired
        validated={!endMeta.touched || !endMeta.error ? 'default' : 'error'}
        label={t`End`}
      >
        <Radio
          id="end-never"
          name="end"
          label={t`Never`}
          value="never"
          isChecked={end.value === 'never'}
          onChange={(value, event) => {
            event.target.value = 'never';
            end.onChange(event);
          }}
          ouiaId="end-never-radio-button"
        />
        <Radio
          id="end-after"
          name="end"
          label={t`After number of occurrences`}
          value="after"
          isChecked={end.value === 'after'}
          onChange={(value, event) => {
            event.target.value = 'after';
            end.onChange(event);
          }}
          ouiaId="end-after-radio-button"
        />
        <Radio
          id="end-on-date"
          name="end"
          label={t`On date`}
          value="onDate"
          isChecked={end.value === 'onDate'}
          onChange={(value, event) => {
            event.target.value = 'onDate';
            end.onChange(event);
          }}
          ouiaId="end-on-radio-button"
        />
      </FormGroup>
      {end?.value === 'after' && (
        <FormField
          id="schedule-occurrences"
          label={t`Occurrences`}
          name="occurrences"
          type="number"
          min="1"
          step="1"
          validate={required(null)}
          isRequired
        />
      )}
      {end?.value === 'onDate' && (
        <DateTimePicker
          dateFieldName={dateFieldName}
          timeFieldName={timeFieldName}
          label={t`End date/time`}
        />
      )}
    </>
  );
};

export default FrequencyDetailSubform;
