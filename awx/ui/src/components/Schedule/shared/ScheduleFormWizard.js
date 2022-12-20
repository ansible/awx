import React from 'react';
import {
  Button,
  FormGroup,
  TextInput,
  Title,
  Wizard,
  WizardContextConsumer,
  WizardFooter,
} from '@patternfly/react-core';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { RRule } from 'rrule';
import { useField, useFormikContext } from 'formik';
import { DateTime } from 'luxon';
import { formatDateString } from 'util/dates';
import FrequencySelect from './FrequencySelect';
import MonthandYearForm from './MonthandYearForm';
import OrdinalDayForm from './OrdinalDayForm';
import WeekdayForm from './WeekdayForm';
import ScheduleEndForm from './ScheduleEndForm';
import parseRuleObj from './parseRuleObj';
import { buildDtStartObj } from './buildRuleObj';

const GroupWrapper = styled(FormGroup)`
  && .pf-c-form__group-control {
    display: flex;
    padding-top: 10px;
  }
  && .pf-c-form__group-label {
    padding-top: 20px;
  }
`;

function ScheduleFormWizard({ isOpen, setIsOpen }) {
  const { values, resetForm, initialValues } = useFormikContext();
  const [freq, freqMeta] = useField('freq');
  const [{ value: frequenciesValue }] = useField('frequencies');
  const [interval, , intervalHelpers] = useField('interval');

  const handleSubmit = (goToStepById) => {
    const {
      name,
      description,
      endingType,
      endTime,
      endDate,
      timezone,
      startDate,
      startTime,
      frequencies,
      ...rest
    } = values;
    if (endingType === 'onDate') {
      const dt = DateTime.fromFormat(
        `${endDate} ${endTime}`,
        'yyyy-MM-dd h:mm a',
        {
          zone: timezone,
        }
      );
      rest.until = formatDateString(dt, timezone);

      delete rest.count;
    }
    if (endingType === 'never') delete rest.count;

    const rule = new RRule(rest);

    const start = buildDtStartObj({
      startDate: values.startDate,
      startTime: values.startTime,
      timezone: values.timezone,
      frequency: values.freq,
    });
    const newFrequency = parseRuleObj({
      timezone,
      frequency: freq.value,
      rrule: rule.toString(),
      dtstart: start,
    });
    if (goToStepById) {
      goToStepById(1);
    }

    resetForm({
      values: {
        ...initialValues,
        description: values.description,
        name: values.name,
        startDate: values.startDate,
        startTime: values.startTime,
        timezone: values.timezone,
        frequencies: frequenciesValue[0].frequency.length
          ? [...frequenciesValue, newFrequency]
          : [newFrequency],
      },
    });
  };
  const CustomFooter = (
    <WizardFooter>
      <WizardContextConsumer>
        {({ activeStep, onNext, onBack, goToStepById }) => (
          <>
            {activeStep.id === 2 ? (
              <>
                <Button
                  variant="primary"
                  onClick={() => {
                    handleSubmit(true, goToStepById);
                  }}
                >{t`Finish and create new`}</Button>
                <Button
                  variant="secondary"
                  onClick={() => {
                    handleSubmit(false);
                    setIsOpen(false);
                  }}
                >{t`Finish and close`}</Button>
              </>
            ) : (
              <Button variant="primary" onClick={onNext}>{t`Next`}</Button>
            )}

            <Button variant="secondary" onClick={onBack}>{t`Back`}</Button>
            <Button
              variant="plain"
              onClick={() => {
                setIsOpen(false);
                resetForm({
                  values: {
                    ...initialValues,
                    description: values.description,
                    name: values.name,
                    startDate: values.startDate,
                    startTime: values.startTime,
                    timezone: values.timezone,
                    frequencies: values.frequencies,
                  },
                });
              }}
            >{t`Cancel`}</Button>
          </>
        )}
      </WizardContextConsumer>
    </WizardFooter>
  );

  return (
    <Wizard
      onClose={() => setIsOpen(false)}
      isOpen={isOpen}
      footer={CustomFooter}
      steps={[
        {
          key: 'frequency',
          name: 'Frequency',
          id: 1,
          component: (
            <>
              <Title size="md" headingLevel="h4">{t`Repeat frequency`}</Title>
              <GroupWrapper
                name="freq"
                fieldId="schedule-frequency"
                isRequired
                helperTextInvalid={freqMeta.error}
                validated={
                  !freqMeta.touched || !freqMeta.error ? 'default' : 'error'
                }
                label={<b>{t`Frequency`}</b>}
              >
                <FrequencySelect />
              </GroupWrapper>
              <GroupWrapper isRequired label={<b>{t`Interval`}</b>}>
                <TextInput
                  type="number"
                  value={interval.value}
                  placeholder={t`Choose an interval for the schedule`}
                  aria-label={t`Choose an interval for the schedule`}
                  onChange={(v) => intervalHelpers.setValue(v)}
                />
              </GroupWrapper>
              <WeekdayForm />
              <MonthandYearForm />
              <OrdinalDayForm />
            </>
          ),
        },
        {
          name: 'End',
          key: 'end',
          id: 2,
          component: <ScheduleEndForm />,
        },
      ]}
    />
  );
}
export default ScheduleFormWizard;
