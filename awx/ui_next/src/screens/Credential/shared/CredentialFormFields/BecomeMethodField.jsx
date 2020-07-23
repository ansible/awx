import React, { useState } from 'react';
import { useField } from 'formik';
import { bool, shape, string } from 'prop-types';
import {
  FormGroup,
  Select,
  SelectOption,
  SelectVariant,
} from '@patternfly/react-core';
import { FieldTooltip } from '../../../../components/FormField';

function BecomeMethodField({ fieldOptions, isRequired }) {
  const [isOpen, setIsOpen] = useState(false);
  const [options, setOptions] = useState(
    [
      'sudo',
      'su',
      'pbrun',
      'pfexec',
      'dzdo',
      'pmrun',
      'runas',
      'enable',
      'doas',
      'ksu',
      'machinectl',
      'sesu',
    ].map(val => ({ value: val }))
  );
  const [becomeMethodField, meta, helpers] = useField({
    name: `inputs.${fieldOptions.id}`,
  });
  return (
    <FormGroup
      fieldId={`credential-${fieldOptions.id}`}
      helperTextInvalid={meta.error}
      label={fieldOptions.label}
      labelIcon={
        fieldOptions.help_text && (
          <FieldTooltip content={fieldOptions.help_text} />
        )
      }
      isRequired={isRequired}
      isValid={!(meta.touched && meta.error)}
    >
      <Select
        maxHeight={200}
        variant={SelectVariant.typeahead}
        onToggle={setIsOpen}
        onClear={() => {
          helpers.setValue('');
        }}
        onSelect={(event, option) => {
          helpers.setValue(option);
          setIsOpen(false);
        }}
        isExpanded={isOpen}
        selections={becomeMethodField.value}
        isCreatable
        onCreateOption={option => {
          setOptions([...options, { value: option }]);
        }}
      >
        {options.map(option => (
          <SelectOption key={option.value} value={option.value} />
        ))}
      </Select>
    </FormGroup>
  );
}
BecomeMethodField.propTypes = {
  fieldOptions: shape({
    id: string.isRequired,
    label: string.isRequired,
  }).isRequired,
  isRequired: bool,
};
BecomeMethodField.defaultProps = {
  isRequired: false,
};

export default BecomeMethodField;
