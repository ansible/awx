import React from 'react';
import { useField } from 'formik';
import { t, Plural } from '@lingui/macro';
import {
  FormGroup,
  TextInput,
  Button,
  InputGroup as PFInputGroup,
  Tooltip,
} from '@patternfly/react-core';
import PFCheckIcon from '@patternfly/react-icons/dist/js/icons/check-icon';
import styled from 'styled-components';
import Popover from '../Popover';
import { required } from '../../util/validators';

const InputGroup = styled(PFInputGroup)`
  padding-bottom: 5px;
`;
const CheckIcon = styled(PFCheckIcon)`
  color: var(--pf-c-button--m-plain--disabled--Color);
  ${props =>
    props.isSelected &&
    `color: var(--pf-c-button--m-secondary--active--Color)`};
`;
function TextAndCheckboxField({ label, tooltip }) {
  const [
    formattedChoicesField,
    formattedChoicesMeta,
    formattedChoicesHelpers,
  ] = useField({
    name: 'formattedChoices',
    validate: required(null),
  });
  const [typeField] = useField('type');
  const isValid =
    !(formattedChoicesMeta.touched && formattedChoicesMeta.error) ||
    formattedChoicesField.value.trim().length > 0;

  return (
    <FormGroup
      helperText={
        <Plural
          value={typeField.value === 'multiselect' ? 2 : 1}
          one="Click checkbox next to an option to mark it as the default value."
          other="Click checkbox next to an option to mark it as a default value."
        />
      }
      hasNoPaddingTop
      helperTextInvalid={formattedChoicesMeta.error}
      label={label}
      isRequired
      onBlur={formattedChoicesHelpers.setTouched}
      validated={isValid ? 'default' : 'error'}
      labelIcon={<Popover content={tooltip} />}
    >
      {formattedChoicesField.value.map(({ choice, isDefault }, i) => (
        <InputGroup>
          <TextInput
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
              // Remove empty string values from formattedChoices from formik and
              // remove the field from the UI.
              if (e.key === 'Backspace' && !choice.trim().length) {
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
          <Tooltip
            content={
              choice
                ? t`Click to select this answer as a default answer.`
                : t`Must type an answer choice before a default value can be selected`
            }
            position="right"
            trigger="mouseenter"
          >
            <Button
              variant="control"
              aria-label={t`Click to toggle default value`}
              ouiaId={choice}
              onClick={() => {
                const newValues = formattedChoicesField.value.map(
                  (cfv, index) =>
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
          </Tooltip>
        </InputGroup>
      ))}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
