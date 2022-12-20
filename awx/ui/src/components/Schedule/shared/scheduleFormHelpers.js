import { t } from '@lingui/macro';
import { DateTime } from 'luxon';
import { RRule } from 'rrule';
import buildRuleObj from './buildRuleObj';
import buildRuleSet from './buildRuleSet';

// const NUM_DAYS_PER_FREQUENCY = {
//   week: 7,
//   month: 31,
//   year: 365,
// };
// const validateSchedule = () =>
// const errors = {};

// values.frequencies.forEach((freq) => {
//   const options = values.frequencyOptions[freq];
//   const freqErrors = {};

//   if (
//     (freq === 'month' || freq === 'year') &&
//     options.runOn === 'day' &&
//     (options.runOnDayNumber < 1 || options.runOnDayNumber > 31)
//   ) {
//     freqErrors.runOn = t`Please select a day number between 1 and 31.`;
//   }

//   if (options.end === 'after' && !options.occurrences) {
//     freqErrors.occurrences = t`Please enter a number of occurrences.`;
//   }

//   if (options.end === 'onDate') {
//     if (
//       DateTime.fromFormat(
//         `${values.startDate} ${values.startTime}`,
//         'yyyy-LL-dd h:mm a'
//       ).toMillis() >=
//       DateTime.fromFormat(
//         `${options.endDate} ${options.endTime}`,
//         'yyyy-LL-dd h:mm a'
//       ).toMillis()
//     ) {
//       freqErrors.endDate = t`Please select an end date/time that comes after the start date/time.`;
//     }

//     if (
//       DateTime.fromISO(options.endDate)
//         .diff(DateTime.fromISO(values.startDate), 'days')
//         .toObject().days < NUM_DAYS_PER_FREQUENCY[freq]
//     ) {
//       const rule = new RRule(
//         buildRuleObj({
//           startDate: values.startDate,
//           startTime: values.startTime,
//           frequencies: freq,
//           ...options,
//         })
//       );
//       if (rule.all().length === 0) {
//         errors.startDate = t`Selected date range must have at least 1 schedule occurrence.`;
//         freqErrors.endDate = t`Selected date range must have at least 1 schedule occurrence.`;
//       }
//     }
//   }
//   if (Object.keys(freqErrors).length > 0) {
//     if (!errors.frequencyOptions) {
//       errors.frequencyOptions = {};
//     }
//     errors.frequencyOptions[freq] = freqErrors;
//   }
// });

// if (values.exceptionFrequency.length > 0 && !scheduleHasInstances(values)) {
//   errors.exceptionFrequency = t`This schedule has no occurrences due to the
// selected exceptions.`;
// }

// ({});
// function scheduleHasInstances(values) {
//   let rangeToCheck = 1;
//   values.frequencies.forEach((freq) => {
//     if (NUM_DAYS_PER_FREQUENCY[freq] > rangeToCheck) {
//       rangeToCheck = NUM_DAYS_PER_FREQUENCY[freq];
//     }
//   });

//   const ruleSet = buildRuleSet(values, true);
//   const startDate = DateTime.fromISO(values.startDate);
//   const endDate = startDate.plus({ days: rangeToCheck });
//   const instances = ruleSet.between(
//     startDate.toJSDate(),
//     endDate.toJSDate(),
//     true,
//     (date, i) => i === 0
//   );

//   return instances.length > 0;
// }

const bysetposOptions = [
  { value: '', key: 'none', label: 'None' },
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
];

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

const weekdayOptions = [
  {
    value: RRule.SU,
    key: 'sunday',
    label: t`Sunday`,
  },
  {
    value: RRule.MO,
    key: 'monday',
    label: t`Monday`,
  },
  {
    value: RRule.TU,
    key: 'tuesday',
    label: t`Tuesday`,
  },
  {
    value: RRule.WE,
    key: 'wednesday',
    label: t`Wednesday`,
  },
  {
    value: RRule.TH,
    key: 'thursday',
    label: t`Thursday`,
  },
  {
    value: RRule.FR,
    key: 'friday',
    label: t`Friday`,
  },
  {
    value: RRule.SA,
    key: 'saturday',
    label: t`Saturday`,
  },
];

const FREQUENCIESCONSTANTS = {
  minute: RRule.MINUTELY,
  hour: RRule.HOURLY,
  day: RRule.DAILY,
  week: RRule.WEEKLY,
  month: RRule.MONTHLY,
  year: RRule.YEARLY,
};
export {
  monthOptions,
  weekdayOptions,
  bysetposOptions,
  // validateSchedule,
  FREQUENCIESCONSTANTS,
};
