import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { RRule } from 'rrule';
import { Select, SelectOption, SelectVariant } from '@patternfly/react-core';

export default function FrequencySelect({ id, onBlur, placeholderText }) {
  const [isOpen, setIsOpen] = useState(false);
  const [frequency, , frequencyHelpers] = useField('freq');

  const onToggle = (val) => {
    if (!val) {
      onBlur();
    }
    setIsOpen(val);
  };

  return (
    <Select
      onSelect={(e, v) => {
        frequencyHelpers.setValue(v);
        setIsOpen(false);
      }}
      selections={frequency.value}
      placeholderText={placeholderText}
      onToggle={onToggle}
      value={frequency.value}
      isOpen={isOpen}
      ouiaId={`frequency-select-${id}`}
      onBlur={() => frequencyHelpers.setTouched(true)}
    >
      <SelectOption value={RRule.MINUTELY}>{t`Minute`}</SelectOption>
      <SelectOption value={RRule.HOURLY}>{t`Hour`}</SelectOption>
      <SelectOption value={RRule.DAILY}>{t`Day`}</SelectOption>
      <SelectOption value={RRule.WEEKLY}>{t`Week`}</SelectOption>
      <SelectOption value={RRule.MONTHLY}>{t`Month`}</SelectOption>
      <SelectOption value={RRule.YEARLY}>{t`Year`}</SelectOption>
    </Select>
  );
}

export { SelectOption, SelectVariant };
