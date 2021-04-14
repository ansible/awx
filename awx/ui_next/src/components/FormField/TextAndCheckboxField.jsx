import React, { useState } from 'react';
import { useField, useFormikContext } from 'formik';

import { Checkbox, FormGroup, TextInput, Radio } from '@patternfly/react-core';
import styled from 'styled-components';
import Popover from '../Popover';

const InputWrapper = styled.span`
  && {
    display: flex;
    padding-bottom: 20px;
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
  rows,
  ...rest
}) {
  const { values: formikValues } = useFormikContext();
  const [choicesField, choicesMeta, choicesHelpers] = useField('choices');
  // const [fields, setFields] = useState(choicesField.value.split('\n'));
  // const [defaultValue, setDefaultValue] = useState(
  //   formikValues.default.split('\n')
  // );
  const [, , defaultHelpers] = useField('default');

  const [isNewValueChecked, setIsNewValueChecked] = useState(false);
  console.log('set');
  const choicesSplit = choicesField.value.split('\n');
  const defaultSplit = formikValues.default.split('\n');
  return (
    <FormGroup
      fieldId={id}
      helperText={helperText}
      helperTextInvalid={choicesMeta.error}
      isRequired={isRequired}
      validated={isValid ? 'default' : 'error'}
      label={label}
      labelIcon={<Popover content={tooltip} />}
    >
      {choicesSplit
        .map((v, i) => (
          <InputWrapper>
            {formikValues.type === 'multiselect' ? (
              <Checkbox
                isChecked={defaultSplit.includes(v)}
                onChange={() =>
                  defaultSplit.includes(v)
                    ? defaultHelpers.setValue(
                        defaultSplit.filter(d => d !== v).join('\n')
                      )
                    : defaultHelpers.setValue(
                        formikValues.default.concat(`\n${v}`)
                      )
                }
              />
            ) : (
              <Radio
                isChecked={defaultSplit.includes(v)}
                onChange={defaultHelpers.setValue(`${v}`)}
              />
            )}
            <TextInput
              id={id}
              isRequired={isRequired}
              validated={isValid ? 'default' : 'error'}
              value={v}
              onChange={value => {
                defaultHelpers.setValue(
                  defaultSplit.filter(d => d !== v).join('\n')
                );

                const newFields = choicesSplit
                  .map((choice, index) => (i === index ? value : choice))
                  .join('\n');

                return value === ''
                  ? choicesHelpers.setValue(
                      choicesSplit.filter(d => d !== v).join('\n')
                    )
                  : choicesHelpers.setValue(newFields);
              }}
            />
          </InputWrapper>
        ))
        .concat(
          <InputWrapper>
            {formikValues.type === 'multiselect' ? (
              <Checkbox
                isChecked={isNewValueChecked}
                onChange={setIsNewValueChecked}
              />
            ) : (
              <Radio
                isChecked={isNewValueChecked}
                onChange={setIsNewValueChecked}
              />
            )}
            <TextInput
              id={id}
              isRequired={isRequired}
              validated={isValid ? 'default' : 'error'}
              value=""
              onChange={(value, event) => {
                choicesHelpers.setValue([...choicesSplit, value].join('\n'));
              }}
            />
          </InputWrapper>
        )}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
