import React, { useState } from 'react';
import { useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import { FormGroup, TextInput, Button } from '@patternfly/react-core';
import PFCheckIcon from '@patternfly/react-icons/dist/js/icons/check-icon';
import styled from 'styled-components';
import Popover from '../Popover';

const InputWrapper = styled.span`
  && {
    display: flex;
    padding-bottom: 5px;
  }
`;
const CheckIcon = styled(PFCheckIcon)`
  color: var(--pf-c-button--m-plain--disabled--Color);
  ${props =>
    props.isSelected &&
    `color: var(--pf-c-button--m-secondary--active--Color)`};
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

  const handleCheckboxChange = v =>
    defaultSplit.includes(v)
      ? defaultHelpers.setValue(defaultSplit.filter(d => d !== v).join('\n'))
      : defaultHelpers.setValue(formikValues.default.concat(`\n${v}`));
  const choicesSplit = choicesField.value.split('\n');
  const defaultSplit = formikValues.default.split('\n');
  return (
    <FormGroup
      helperText={helperText}
      helperTextInvalid={choicesMeta.error}
      label={label}
      labelIcon={<Popover content={tooltip} />}
    >
      {choicesSplit
        .map((v, i) => (
          <InputWrapper>
            <TextInput
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
            <Button
              variant="control"
              aria-label={t`Click to toggle default value`}
              ouiaId={v}
              onClick={() =>
                formikValues.type === 'multiselect'
                  ? handleCheckboxChange(v)
                  : defaultHelpers.setValue(`${v}`)
              }
            >
              <CheckIcon isSelected={defaultSplit.includes(v)} />
            </Button>
          </InputWrapper>
        ))
        .concat(
          <InputWrapper>
            <TextInput
              value=""
              onChange={(value, event) => {
                choicesHelpers.setValue([...choicesSplit, value].join('\n'));
              }}
            />
            <Button
              variant="control"
              aria-label={t`Click to toggle default value`}
              ouiaId="new input"
              onClick={
                () => {}
                // formikValues.type === 'multiselect'
                //   ? handleCheckboxChange(v)
                //   : defaultHelpers.setValue(`${v}`)
              }
            >
              <CheckIcon isSelected={false} />
            </Button>
          </InputWrapper>
        )}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
