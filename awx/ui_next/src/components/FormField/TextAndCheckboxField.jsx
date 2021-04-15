import React from 'react';
import { useField } from 'formik';
import { t } from '@lingui/macro';
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

const InputGroup = styled(PFInputGroup)`
  padding-bottom: 5px;
`;
const CheckIcon = styled(PFCheckIcon)`
  color: var(--pf-c-button--m-plain--disabled--Color);
  ${props =>
    props.isSelected &&
    `color: var(--pf-c-button--m-secondary--active--Color)`};
`;
function TextAndCheckboxField({ label, helperText, tooltip }) {
  const [choicesField, choicesMeta, choicesHelpers] = useField('choices');
  const [typeField] = useField('type');
  const [defaultField, , defaultHelpers] = useField('default');

  const handleCheckboxChange = v =>
    defaultSplit.includes(v)
      ? defaultHelpers.setValue(defaultSplit.filter(d => d !== v).join('\n'))
      : defaultHelpers.setValue(defaultField.value.concat(`\n${v}`));
  const choicesSplit = choicesField.value.split('\n');
  const defaultSplit = defaultField.value?.split('\n');
  return (
    <FormGroup
      helperText={helperText}
      helperTextInvalid={choicesMeta.error}
      label={label}
      labelIcon={<Popover content={tooltip} />}
    >
      {choicesSplit.map((v, i) => (
        <InputGroup>
          <TextInput
            onKeyDown={e => {
              if (e.key === 'Enter' && i === choicesSplit.length - 1) {
                choicesHelpers.setValue(choicesField.value.concat('\n'));
              }

              if (e.key === 'Backspace' && v.length <= 1) {
                const removeEmptyField = choicesSplit
                  .filter((choice, index) => index !== i)
                  .join('\n');
                choicesHelpers.setValue(removeEmptyField);
              }
            }}
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
          <Tooltip
            content={t`Click to select this answer as a default answer.`}
            position="right"
            trigger="mouseenter"
          >
            <Button
              variant="control"
              aria-label={t`Click to toggle default value`}
              ouiaId={v}
              onClick={() =>
                typeField.value === 'multiselect'
                  ? handleCheckboxChange(v)
                  : defaultHelpers.setValue(`${v}`)
              }
            >
              <CheckIcon isSelected={defaultSplit?.includes(v) || false} />
            </Button>
          </Tooltip>
        </InputGroup>
      ))}
    </FormGroup>
  );
}

export default TextAndCheckboxField;
