import React, { useState } from 'react';
import { useField } from 'formik';

import { Checkbox, FormGroup, TextInput } from '@patternfly/react-core';
import styled from 'styled-components';
import Popover from '../Popover';

const InputWrapper = styled.span`
  && {
    display: flex;
  }
`;
function TextAndCheckboxField({
  id,
  label,
  helperText,
  isRequired,
  isValid,
  tooltip,
  name,
  type,
  rows,
  ...rest
}) {
  const [field, meta] = useField({ name });
  const [fields, setFields] = useState(field.value.split('\n'));
  let array = field.value.split('\n');

  return (
    <FormGroup
      fieldId={id}
      helperText={helperText}
      helperTextInvalid={meta.error}
      isRequired={isRequired}
      validated={isValid ? 'default' : 'error'}
      label={label}
      labelIcon={<Popover content={tooltip} />}
    >
      {fields
        .map((v, i) => (
          <InputWrapper>
            <Checkbox />
            <TextInput
              id={id}
              isRequired={isRequired}
              validated={isValid ? 'default' : 'error'}
              value={v}
              type={type}
              onChange={value => {
                if (value === '') {
                  setFields(fields.filter((f, index) => i !== index));
                } else {
                  setFields(
                    fields.map((f, index) => {
                      if (i === index) {
                        return value;
                      }
                      return f;
                    })
                  );
                }
              }}
            />
          </InputWrapper>
        ))
        .concat(
          <InputWrapper>
            <Checkbox />
            <TextInput
              id={id}
              isRequired={isRequired}
              validated={isValid ? 'default' : 'error'}
              value=""
              type={type}
              onChange={(value, event) => {
                setFields([...fields, value]);
              }}
            />
          </InputWrapper>
        )}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
