import React from 'react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { useField } from 'formik';
import { FormGroup, TextInput } from '@patternfly/react-core';

const GroupWrapper = styled(FormGroup)`
  && .pf-c-form__group-control {
    display: flex;
    padding-top: 10px;
  }
  && .pf-c-form__group-label {
    padding-top: 20px;
  }
`;

function OrdinalDayForm() {
  const [byMonthDay] = useField('bymonthday');
  const [byYearDay] = useField('byyearday');
  return (
    <GroupWrapper
      label={<b>{t`On a specific number day`}</b>}
      name="ordinalDay"
    >
      <TextInput
        placeholder={t`Run on a day of month`}
        aria-label={t`Type a numbered day`}
        type="number"
        onChange={(value, event) => {
          byMonthDay.onChange(event);
        }}
      />
      <TextInput
        placeholder={t`Run on a day of year`}
        aria-label={t`Type a numbered day`}
        type="number"
        onChange={(value, event) => {
          byYearDay.onChange(event);
        }}
      />
    </GroupWrapper>
  );
}

export default OrdinalDayForm;
