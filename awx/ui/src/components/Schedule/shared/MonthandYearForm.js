import React from 'react';
import { t } from '@lingui/macro';
import AnsibleSelect from 'components/AnsibleSelect';
import styled from 'styled-components';
import {
  FormGroup,
  Checkbox as _Checkbox,
  Grid,
  GridItem,
} from '@patternfly/react-core';
import { useField } from 'formik';
import { bysetposOptions, monthOptions } from './scheduleFormHelpers';

const GroupWrapper = styled(FormGroup)`
  && .pf-c-form__group-control {
    display: flex;
    padding-top: 10px;
  }
  && .pf-c-form__group-label {
    padding-top: 20px;
  }
`;
const Checkbox = styled(_Checkbox)`
  :not(:last-of-type) {
    margin-right: 10px;
  }
`;
function MonthandYearForm({ id }) {
  const [bySetPos, , bySetPosHelpers] = useField('bysetpos');
  const [byMonth, , byMonthHelpers] = useField('bymonth');

  return (
    <>
      <GroupWrapper
        fieldId={`schedule-run-on-${id}`}
        label={<b>{t`Run on a specific month`}</b>}
      >
        <Grid hasGutter>
          {monthOptions.map((month) => (
            <GridItem key={month.label} span={2} rowSpan={2}>
              <Checkbox
                label={month.label}
                isChecked={byMonth.value?.includes(month.value)}
                onChange={(checked) => {
                  if (checked) {
                    byMonthHelpers.setValue([...byMonth.value, month.value]);
                  } else {
                    const removed = byMonth.value.filter(
                      (i) => i !== month.value
                    );
                    byMonthHelpers.setValue(removed);
                  }
                }}
                id={`bymonth-${month.label}`}
                ouiaId={`bymonth-${month.label}`}
                name="bymonth"
              />
            </GridItem>
          ))}
        </Grid>
      </GroupWrapper>
      <GroupWrapper
        label={<b>{t`Run on a specific week day at monthly intervals`}</b>}
      >
        <AnsibleSelect
          id={`schedule-run-on-the-occurrence-${id}`}
          data={bysetposOptions}
          {...bySetPos}
          onChange={(e, v) => {
            bySetPosHelpers.setValue(v);
          }}
        />
      </GroupWrapper>
    </>
  );
}
export default MonthandYearForm;
