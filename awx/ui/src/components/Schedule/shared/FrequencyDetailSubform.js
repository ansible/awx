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
import { required, requiredPositiveInteger } from 'util/validators';
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

const FrequencyDetailSubform = ({ frequency, prefix, isException }) => {
  const id = prefix.replace('.', '-');
  const [runOnDayMonth] = useField({
    name: `${prefix}.runOnDayMonth`,
  });
  const [runOnDayNumber] = useField({
    name: `${prefix}.runOnDayNumber`,
  });
  const [runOnTheOccurrence] = useField({
    name: `${prefix}.runOnTheOccurrence`,
  });
  const [runOnTheDay] = useField({
    name: `${prefix}.runOnTheDay`,
  });
  const [runOnTheMonth] = useField({
    name: `${prefix}.runOnTheMonth`,
  });
  const [startDate] = useField(`${prefix}.startDate`);

  const [daysOfWeek, daysOfWeekMeta, daysOfWeekHelpers] = useField({
    name: `${prefix}.daysOfWeek`,
    validate: (val) => {
      if (frequency === 'week') {
        return required(t`Select a value for this field`)(val?.length > 0);
      }
      return undefined;
    },
  });
  const [end, endMeta] = useField({
    name: `${prefix}.end`,
    validate: required(t`Select a value for this field`),
  });
  const [interval, intervalMeta] = useField({
    name: `${prefix}.interval`,
    validate: requiredPositiveInteger(),
  });
  const [runOn, runOnMeta] = useField({
    name: `${prefix}.runOn`,
    validate: (val) => {
      if (frequency === 'month' || frequency === 'year') {
        return required(t`Select a value for this field`)(val);
      }
      return undefined;
    },
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
    const newDaysOfWeek = daysOfWeek.value ? [...daysOfWeek.value] : [];
    daysOfWeekHelpers.setTouched(true);
    if (checked) {
      newDaysOfWeek.push(day);
      daysOfWeekHelpers.setValue(newDaysOfWeek);
    } else {
      daysOfWeekHelpers.setValue(
        newDaysOfWeek.filter((selectedDay) => selectedDay !== day)
      );
    }
  };

  const getPeriodLabel = () => {
    switch (frequency) {
      case 'minute':
        return t`Minute`;
      case 'hour':
        return t`Hour`;
      case 'day':
        return t`Day`;
      case 'week':
        return t`Week`;
      case 'month':
        return t`Month`;
      case 'year':
        return t`Year`;
      default:
        throw new Error(t`Frequency did not match an expected value`);
    }
  };

  const getRunEveryLabel = () => {
    const intervalValue = interval.value;

    switch (frequency) {
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

  return (
    <>
      <p css="grid-column: 1/-1">
        <b>{getPeriodLabel()}</b>
      </p>
      <FormGroup
        name={`${prefix}.interval`}
        fieldId={`schedule-run-every-${id}`}
        helperTextInvalid={intervalMeta.error}
        isRequired
        validated={
          !intervalMeta.touched || !intervalMeta.error ? 'default' : 'error'
        }
        label={isException ? t`Skip every` : t`Run every`}
      >
        <div css="display: flex">
          <TextInput
            css="margin-right: 10px;"
            id={`schedule-run-every-${id}`}
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
      {frequency === 'week' && (
        <FormGroup
          name={`${prefix}.daysOfWeek`}
          fieldId={`schedule-days-of-week-${id}`}
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
              isChecked={daysOfWeek.value?.includes(RRule.SU)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.SU, checked);
              }}
              aria-label={t`Sunday`}
              id={`schedule-days-of-week-sun-${id}`}
              ouiaId={`schedule-days-of-week-sun-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Mon`}
              isChecked={daysOfWeek.value?.includes(RRule.MO)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.MO, checked);
              }}
              aria-label={t`Monday`}
              id={`schedule-days-of-week-mon-${id}`}
              ouiaId={`schedule-days-of-week-mon-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Tue`}
              isChecked={daysOfWeek.value?.includes(RRule.TU)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.TU, checked);
              }}
              aria-label={t`Tuesday`}
              id={`schedule-days-of-week-tue-${id}`}
              ouiaId={`schedule-days-of-week-tue-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Wed`}
              isChecked={daysOfWeek.value?.includes(RRule.WE)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.WE, checked);
              }}
              aria-label={t`Wednesday`}
              id={`schedule-days-of-week-wed-${id}`}
              ouiaId={`schedule-days-of-week-wed-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Thu`}
              isChecked={daysOfWeek.value?.includes(RRule.TH)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.TH, checked);
              }}
              aria-label={t`Thursday`}
              id={`schedule-days-of-week-thu-${id}`}
              ouiaId={`schedule-days-of-week-thu-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Fri`}
              isChecked={daysOfWeek.value?.includes(RRule.FR)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.FR, checked);
              }}
              aria-label={t`Friday`}
              id={`schedule-days-of-week-fri-${id}`}
              ouiaId={`schedule-days-of-week-fri-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
            <Checkbox
              label={t`Sat`}
              isChecked={daysOfWeek.value?.includes(RRule.SA)}
              onChange={(checked) => {
                updateDaysOfWeek(RRule.SA, checked);
              }}
              aria-label={t`Saturday`}
              id={`schedule-days-of-week-sat-${id}`}
              ouiaId={`schedule-days-of-week-sat-${id}`}
              name={`${prefix}.daysOfWeek`}
            />
          </div>
        </FormGroup>
      )}
      {(frequency === 'month' || frequency === 'year') &&
        !Number.isNaN(new Date(startDate.value)) && (
          <FormGroup
            name={`${prefix}.runOn`}
            fieldId={`schedule-run-on-${id}`}
            helperTextInvalid={runOnMeta.error}
            isRequired
            validated={
              !runOnMeta.touched || !runOnMeta.error ? 'default' : 'error'
            }
            label={t`Run on`}
          >
            <RunOnRadio
              id={`schedule-run-on-day-${id}`}
              name={`${prefix}.runOn`}
              label={
                <div css="display: flex;align-items: center;">
                  {frequency === 'month' && (
                    <span
                      id="radio-schedule-run-on-day"
                      css="margin-right: 10px;"
                    >
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
        )}
      <FormGroup
        name={`${prefix}.end`}
        fieldId={`schedule-end-${id}`}
        helperTextInvalid={endMeta.error}
        isRequired
        validated={!endMeta.touched || !endMeta.error ? 'default' : 'error'}
        label={t`End`}
      >
        <Radio
          id={`end-never-${id}`}
          name={`${prefix}.end`}
          label={t`Never`}
          value="never"
          isChecked={end.value === 'never'}
          onChange={(value, event) => {
            event.target.value = 'never';
            end.onChange(event);
          }}
          ouiaId={`end-never-radio-button-${id}`}
        />
        <Radio
          id={`end-after-${id}`}
          name={`${prefix}.end`}
          label={t`After number of occurrences`}
          value="after"
          isChecked={end.value === 'after'}
          onChange={(value, event) => {
            event.target.value = 'after';
            end.onChange(event);
          }}
          ouiaId={`end-after-radio-button-${id}`}
        />
        <Radio
          id={`end-on-date-${id}`}
          name={`${prefix}.end`}
          label={t`On date`}
          value="onDate"
          isChecked={end.value === 'onDate'}
          onChange={(value, event) => {
            event.target.value = 'onDate';
            end.onChange(event);
          }}
          ouiaId={`end-on-radio-button-${id}`}
        />
      </FormGroup>
      {end?.value === 'after' && (
        <FormField
          id={`schedule-occurrences-${id}`}
          label={t`Occurrences`}
          name={`${prefix}.occurrences`}
          type="number"
          min="1"
          step="1"
          isRequired
        />
      )}
      {end?.value === 'onDate' && (
        <DateTimePicker
          dateFieldName={`${prefix}.endDate`}
          timeFieldName={`${prefix}.endTime`}
          label={t`End date/time`}
        />
      )}
    </>
  );
};

export default FrequencyDetailSubform;
