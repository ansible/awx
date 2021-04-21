import React from 'react';
import { useField } from 'formik';
import { t } from '@lingui/macro';
import {
  FormGroup,
  TextInput,
  Button,
  InputGroup as PFInputGroup,
} from '@patternfly/react-core';
import PFCheckIcon from '@patternfly/react-icons/dist/js/icons/check-icon';
import styled from 'styled-components';
import Popover from '../Popover';

const InputGroup = styled(PFInputGroup)`
  padding-bottom: 5px;
`;
const CheckIcon = styled(PFCheckIcon)`
  color: var(--pf-c-button--m-plain--disabled--Color);
  ${props =>
    props.isSelected &&
    `color: var(--pf-c-button--m-secondary--active--Color)`};
`;

const validate = () => {
  return value => {
    let message;
    const hasValue = value.find(({ choice }) =>
      choice.trim().length > 0 ? choice : undefined
    );
    if (!hasValue) {
      message = t`There must be a value in at least one input`;
    }
    return message;
  };
};
function TextAndCheckboxField({ label, tooltip }) {
  const [
    formattedChoicesField,
    formattedChoicesMeta,
    formattedChoicesHelpers,
  ] = useField({
    name: 'formattedChoices',
    validate: validate(),
  });

  const [typeField] = useField('type');
  const isValid = !(formattedChoicesMeta.touched && formattedChoicesMeta.error);

  return (
    <FormGroup
      label={label}
      isRequired
      helperText={
        !formattedChoicesField.value[0].choice.trim().length
          ? t`Type answer then click checkbox on right to select answer as default.`
          : t`Press 'Enter' to add more answer choices. One answer choice per line. `
      }
      helperTextInvalid={formattedChoicesMeta.error}
      onBlur={e => {
        if (!e.currentTarget.contains(e.relatedTarget)) {
          formattedChoicesHelpers.setTouched();
        }
      }}
      validated={isValid ? 'default' : 'error'}
      labelIcon={<Popover content={tooltip} />}
    >
      {formattedChoicesField.value.map(({ choice, isDefault }, i) => (
        <InputGroup>
          <TextInput
            aria-label={choice}
            onKeyUp={e => {
              if (
                e.key === 'Enter' &&
                choice.trim().length > 0 &&
                i === formattedChoicesField.value.length - 1
              ) {
                formattedChoicesHelpers.setValue(
                  formattedChoicesField.value.concat({
                    choice: '',
                    isDefault: false,
                  })
                );
              }

              if (
                e.key === 'Backspace' &&
                !choice.trim() &&
                formattedChoicesField.value.length > 1
              ) {
                const removeEmptyField = formattedChoicesField.value.filter(
                  (c, index) => index !== i
                );

                formattedChoicesHelpers.setValue(removeEmptyField);
              }
            }}
            value={choice}
            onChange={value => {
              const newValues = formattedChoicesField.value.map((cfv, index) =>
                i === index ? { choice: value, isDefault: false } : cfv
              );
              formattedChoicesHelpers.setValue(newValues);
            }}
          />

          <Button
            variant="control"
            aria-label={t`Click to toggle default value`}
            ouiaId={choice}
            isDisabled={!choice.trim()}
            onClick={() => {
              const newValues = formattedChoicesField.value.map((cfv, index) =>
                i === index
                  ? { choice: cfv.choice, isDefault: !cfv.isDefault }
                  : cfv
              );
              const singleSelectValues = formattedChoicesField.value.map(
                (cfv, index) =>
                  i === index
                    ? { choice: cfv.choice, isDefault: !cfv.isDefault }
                    : { choice: cfv.choice, isDefault: false }
              );
              return typeField.value === 'multiplechoice'
                ? formattedChoicesHelpers.setValue(singleSelectValues)
                : formattedChoicesHelpers.setValue(newValues);
            }}
          >
            <CheckIcon isSelected={isDefault} />
          </Button>
        </InputGroup>
      ))}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
