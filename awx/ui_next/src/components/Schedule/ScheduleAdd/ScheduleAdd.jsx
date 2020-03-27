import React, { useState } from 'react';
import { func } from 'prop-types';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { useHistory, useLocation } from 'react-router-dom';
import { RRule } from 'rrule';
import { Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import { getWeekNumber } from '@util/dates';
import ScheduleForm from '../shared/ScheduleForm';

const days = {
  0: 'SU',
  1: 'MO',
  2: 'TU',
  3: 'WE',
  4: 'TH',
  5: 'FR',
  6: 'SA',
};

function ScheduleAdd({ i18n, createSchedule }) {
  const [formSubmitError, setFormSubmitError] = useState(null);
  const history = useHistory();
  const location = useLocation();
  const { pathname } = location;
  const pathRoot = pathname.substr(0, pathname.indexOf('schedules'));

  const buildRuleObj = values => {
    const [startDate, startTime] = values.startDateTime.split('T');
    // Dates are formatted like "YYYY-MM-DD"
    const [startYear, startMonth, startDay] = startDate.split('-');
    // Times are formatted like "HH:MM:SS" or "HH:MM" if no seconds
    // have been specified
    const [startHour = 0, startMinute = 0, startSecond = 0] = startTime.split(
      ':'
    );

    const ruleObj = {
      interval: values.interval,
      dtstart: new Date(
        Date.UTC(
          startYear,
          parseInt(startMonth, 10) - 1,
          startDay,
          startHour,
          startMinute,
          startSecond
        )
      ),
      tzid: values.timezone,
    };

    switch (values.frequency) {
      case 'none':
        ruleObj.count = 1;
        ruleObj.freq = RRule.MINUTELY;
        break;
      case 'minute':
        ruleObj.freq = RRule.MINUTELY;
        break;
      case 'hour':
        ruleObj.freq = RRule.HOURLY;
        break;
      case 'day':
        ruleObj.freq = RRule.DAILY;
        break;
      case 'week':
        ruleObj.freq = RRule.WEEKLY;
        ruleObj.byweekday = values.daysOfWeek.map(day => RRule[day]);
        break;
      case 'month':
        ruleObj.freq = RRule.MONTHLY;
        if (values.runOn === 'number') {
          ruleObj.bymonthday = startDay;
        } else if (values.runOn === 'day') {
          ruleObj.byweekday =
            RRule[days[new Date(values.startDateTime).getDay()]];
          ruleObj.bysetpos = getWeekNumber(values.startDateTime);
        } else if (values.runOn === 'lastDay') {
          ruleObj.byweekday =
            RRule[days[new Date(values.startDateTime).getDay()]];
          ruleObj.bysetpos = -1;
        }
        break;
      case 'year':
        ruleObj.freq = RRule.YEARLY;
        ruleObj.bymonth = new Date(values.startDateTime).getMonth() + 1;
        if (values.runOn === 'number') {
          ruleObj.bymonthday = startDay;
        } else if (values.runOn === 'day') {
          ruleObj.byweekday =
            RRule[days[new Date(values.startDateTime).getDay()]];
          ruleObj.bysetpos = getWeekNumber(values.startDateTime);
        } else if (values.runOn === 'lastDay') {
          ruleObj.byweekday =
            RRule[days[new Date(values.startDateTime).getDay()]];
          ruleObj.bysetpos = -1;
        }
        break;
      default:
        throw new Error(i18n._(t`Frequency did not match an expected value`));
    }

    switch (values.end) {
      case 'never':
        break;
      case 'after':
        ruleObj.count = values.occurrences;
        break;
      case 'onDate': {
        const [endDate, endTime] = values.endDateTime.split('T');
        const [endYear, endMonth, endDay] = endDate.split('-');
        const [endHour = 0, endMinute = 0, endSecond = 0] = endTime.split(':');
        ruleObj.until = new Date(
          Date.UTC(
            endYear,
            parseInt(endMonth, 10) - 1,
            endDay,
            endHour,
            endMinute,
            endSecond
          )
        );
        break;
      }
      default:
        throw new Error(i18n._(t`End did not match an expected value`));
    }

    return ruleObj;
  };

  const handleSubmit = async values => {
    try {
      const rule = new RRule(buildRuleObj(values));
      const {
        data: { id: scheduleId },
      } = await createSchedule({
        name: values.name,
        description: values.description,
        rrule: rule.toString().replace(/\n/g, ' '),
      });

      history.push(`${pathRoot}schedules/${scheduleId}`);
    } catch (err) {
      setFormSubmitError(err);
    }
  };

  return (
    <Card>
      <CardBody>
        <ScheduleForm
          handleCancel={() => history.push(`${pathRoot}schedules`)}
          handleSubmit={handleSubmit}
          submitError={formSubmitError}
        />
      </CardBody>
    </Card>
  );
}

ScheduleAdd.propTypes = {
  createSchedule: func.isRequired,
};

ScheduleAdd.defaultProps = {};

export default withI18n()(ScheduleAdd);
