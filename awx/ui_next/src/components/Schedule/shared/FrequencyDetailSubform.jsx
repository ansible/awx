import React, { useEffect } from 'react';
import styled from 'styled-components';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  Checkbox as _Checkbox,
  FormGroup,
  Radio,
  TextInput,
} from '@patternfly/react-core';
import FormField from '@components/FormField';
import {
  getDaysInMonth,
  getDayString,
  getMonthString,
  getWeekString,
  getWeekNumber,
} from '@util/dates';
import { required } from '@util/validators';

const RunEveryLabel = styled.p`
  display: flex;
  align-items: center;
`;

const Checkbox = styled(_Checkbox)`
  :not(:last-of-type) {
    margin-right: 10px;
  }
`;

export function requiredPositiveInteger(i18n) {
  return value => {
    if (typeof value === 'number') {
      if (!Number.isInteger(value)) {
        return i18n._(t`This field must an integer`);
      }
      if (value < 1) {
        return i18n._(t`This field must be greater than 0`);
      }
    }
    if (!value) {
      return i18n._(t`Select a value for this field`);
    }
    return undefined;
  };
}

const FrequencyDetailSubform = ({ i18n }) => {
  const [startDateTime] = useField({
    name: 'startDateTime',
  });
  const [daysOfWeek, daysOfWeekMeta, daysOfWeekHelpers] = useField({
    name: 'daysOfWeek',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [end, endMeta] = useField({
    name: 'end',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [interval, intervalMeta] = useField({
    name: 'interval',
    validate: requiredPositiveInteger(i18n),
  });
  const [runOn, runOnMeta, runOnHelpers] = useField({
    name: 'runOn',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [endDateTime, endDateTimeMeta] = useField({
    name: 'endDateTime',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [frequency] = useField({
    name: 'frequency',
  });
  useField({
    name: 'occurrences',
    validate: requiredPositiveInteger(i18n),
  });

  useEffect(() => {
    // The Last day option disappears if the start date isn't in the
    // last week of the month.  If that value was selected when this
    // happens then we'll clear out the selection and force the user
    // to choose between the remaining two.
    if (
      (frequency.value === 'month' || frequency.value === 'year') &&
      runOn.value === 'lastDay' &&
      getDaysInMonth(startDateTime.value) - 7 >=
        new Date(startDateTime.value).getDate()
    ) {
      runOnHelpers.setValue('');
    }
  }, [startDateTime.value, frequency.value, runOn.value, runOnHelpers]);

  const updateDaysOfWeek = (day, checked) => {
    const newDaysOfWeek = [...daysOfWeek.value];
    if (checked) {
      newDaysOfWeek.push(day);
      daysOfWeekHelpers.setValue(newDaysOfWeek);
    } else {
      daysOfWeekHelpers.setValue(
        newDaysOfWeek.filter(selectedDay => selectedDay !== day)
      );
    }
  };

  const getRunEveryLabel = () => {
    switch (frequency.value) {
      case 'minute':
        return i18n.plural({
          value: interval.value,
          one: 'minute',
          other: 'minutes',
        });
      case 'hour':
        return i18n.plural({
          value: interval.value,
          one: 'hour',
          other: 'hours',
        });
      case 'day':
        return i18n.plural({
          value: interval.value,
          one: 'day',
          other: 'days',
        });
      case 'week':
        return i18n.plural({
          value: interval.value,
          one: 'week',
          other: 'weeks',
        });
      case 'month':
        return i18n.plural({
          value: interval.value,
          one: 'month',
          other: 'months',
        });
      case 'year':
        return i18n.plural({
          value: interval.value,
          one: 'year',
          other: 'years',
        });
      default:
        throw new Error(i18n._(t`Frequency did not match an expected value`));
    }
  };

  const generateRunOnNumberLabel = () => {
    switch (frequency.value) {
      case 'month':
        return i18n._(
          t`Day ${startDateTime.value.split('T')[0].split('-')[2]}`
        );
      case 'year': {
        const monthString = getMonthString(
          new Date(startDateTime.value).getMonth(),
          i18n
        );
        return `${monthString} ${new Date(startDateTime.value).getDate()}`;
      }
      default:
        throw new Error(i18n._(t`Frequency did not match an expected value`));
    }
  };

  const generateRunOnDayLabel = () => {
    const dayString = getDayString(
      new Date(startDateTime.value).getDay(),
      i18n
    );
    const weekNumber = getWeekNumber(startDateTime.value);
    const weekString = getWeekString(weekNumber, i18n);
    switch (frequency.value) {
      case 'month':
        return i18n._(t`The ${weekString} ${dayString}`);
      case 'year': {
        const monthString = getMonthString(
          new Date(startDateTime.value).getMonth(),
          i18n
        );
        return i18n._(t`The ${weekString} ${dayString} in ${monthString}`);
      }
      default:
        throw new Error(i18n._(t`Frequency did not match an expected value`));
    }
  };

  const generateRunOnLastDayLabel = () => {
    const dayString = getDayString(
      new Date(startDateTime.value).getDay(),
      i18n
    );
    switch (frequency.value) {
      case 'month':
        return i18n._(t`The last ${dayString}`);
      case 'year': {
        const monthString = getMonthString(
          new Date(startDateTime.value).getMonth(),
          i18n
        );
        return i18n._(t`The last ${dayString} in ${monthString}`);
      }
      default:
        throw new Error(i18n._(t`Frequency did not match an expected value`));
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
        isValid={!intervalMeta.touched || !intervalMeta.error}
        label={i18n._(t`Run every`)}
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
          isValid={!daysOfWeekMeta.touched || !daysOfWeekMeta.error}
          label={i18n._(t`On days`)}
        >
          <div css="display: flex">
            <Checkbox
              label={i18n._(t`Sun`)}
              isChecked={daysOfWeek.value.includes('SU')}
              onChange={checked => {
                updateDaysOfWeek('SU', checked);
              }}
              aria-label={i18n._(t`Sunday`)}
              id="days-of-week-sun"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Mon`)}
              isChecked={daysOfWeek.value.includes('MO')}
              onChange={checked => {
                updateDaysOfWeek('MO', checked);
              }}
              aria-label={i18n._(t`Monday`)}
              id="days-of-week-mon"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Tue`)}
              isChecked={daysOfWeek.value.includes('TU')}
              onChange={checked => {
                updateDaysOfWeek('TU', checked);
              }}
              aria-label={i18n._(t`Tuesday`)}
              id="days-of-week-tue"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Wed`)}
              isChecked={daysOfWeek.value.includes('WE')}
              onChange={checked => {
                updateDaysOfWeek('WE', checked);
              }}
              aria-label={i18n._(t`Wednesday`)}
              id="days-of-week-wed"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Thu`)}
              isChecked={daysOfWeek.value.includes('TH')}
              onChange={checked => {
                updateDaysOfWeek('TH', checked);
              }}
              aria-label={i18n._(t`Thursday`)}
              id="days-of-week-thu"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Fri`)}
              isChecked={daysOfWeek.value.includes('FR')}
              onChange={checked => {
                updateDaysOfWeek('FR', checked);
              }}
              aria-label={i18n._(t`Friday`)}
              id="days-of-week-fri"
              name="daysOfWeek"
            />
            <Checkbox
              label={i18n._(t`Sat`)}
              isChecked={daysOfWeek.value.includes('SA')}
              onChange={checked => {
                updateDaysOfWeek('SA', checked);
              }}
              aria-label={i18n._(t`Saturday`)}
              id="days-of-week-sat"
              name="daysOfWeek"
            />
          </div>
        </FormGroup>
      )}
      {(frequency?.value === 'month' || frequency?.value === 'year') &&
        !isNaN(new Date(startDateTime.value)) && (
          <FormGroup
            name="runOn"
            fieldId="schedule-run-on"
            helperTextInvalid={runOnMeta.error}
            isRequired
            isValid={!runOnMeta.touched || !runOnMeta.error}
            label={i18n._(t`Run on`)}
          >
            <Radio
              id="run-on-number"
              name="runOn"
              label={generateRunOnNumberLabel()}
              value="number"
              isChecked={runOn.value === 'number'}
              onChange={(value, event) => {
                event.target.value = 'number';
                runOn.onChange(event);
              }}
            />
            <Radio
              id="run-on-day"
              name="runOn"
              label={generateRunOnDayLabel()}
              value="day"
              isChecked={runOn.value === 'day'}
              onChange={(value, event) => {
                event.target.value = 'day';
                runOn.onChange(event);
              }}
            />
            {new Date(startDateTime.value).getDate() >
              getDaysInMonth(startDateTime.value) - 7 && (
              <Radio
                id="run-on-last-day"
                name="runOn"
                label={generateRunOnLastDayLabel()}
                value="lastDay"
                isChecked={runOn.value === 'lastDay'}
                onChange={(value, event) => {
                  event.target.value = 'lastDay';
                  runOn.onChange(event);
                }}
              />
            )}
          </FormGroup>
        )}
      <FormGroup
        name="end"
        fieldId="schedule-end"
        helperTextInvalid={endMeta.error}
        isRequired
        isValid={!endMeta.touched || !endMeta.error}
        label={i18n._(t`End`)}
      >
        <Radio
          id="end-never"
          name="end"
          label={i18n._(t`Never`)}
          value="never"
          isChecked={end.value === 'never'}
          onChange={(value, event) => {
            event.target.value = 'never';
            end.onChange(event);
          }}
        />
        <Radio
          id="end-after"
          name="end"
          label={i18n._(t`After number of occurrences`)}
          value="after"
          isChecked={end.value === 'after'}
          onChange={(value, event) => {
            event.target.value = 'after';
            end.onChange(event);
          }}
        />
        <Radio
          id="end-on-date"
          name="end"
          label={i18n._(t`On date`)}
          value="onDate"
          isChecked={end.value === 'onDate'}
          onChange={(value, event) => {
            event.target.value = 'onDate';
            end.onChange(event);
          }}
        />
      </FormGroup>
      {end?.value === 'after' && (
        <FormField
          id="schedule-occurrences"
          label={i18n._(t`Occurrences`)}
          name="occurrences"
          type="number"
          min="1"
          step="1"
          validate={required(null, i18n)}
          isRequired
        />
      )}
      {end?.value === 'onDate' && (
        <FormGroup
          fieldId="schedule-end-datetime"
          helperTextInvalid={endDateTimeMeta.error}
          isRequired
          isValid={!endDateTimeMeta.touched || !endDateTimeMeta.error}
          label={i18n._(t`End date/time`)}
        >
          <input
            className="pf-c-form-control"
            type="datetime-local"
            id="schedule-end-datetime"
            step="1"
            {...endDateTime}
          />
        </FormGroup>
      )}
    </>
  );
  /* eslint-enable no-restricted-globals */
};

export default withI18n()(FrequencyDetailSubform);
