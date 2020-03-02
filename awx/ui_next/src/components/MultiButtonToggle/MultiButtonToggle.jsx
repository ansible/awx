import React from 'react';
import { func, string } from 'prop-types';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';
import ButtonGroup from './ButtonGroup';

const SmallButton = styled(Button)`
  padding: 3px 8px;
  font-size: var(--pf-global--FontSize--xs);
`;

function MultiButtonToggle({ buttons, currentValue, onChange }) {
  const setValue = newValue => {
    if (currentValue !== newValue) {
      onChange(newValue);
    }
  };

  return (
    <ButtonGroup>
      {buttons.map(([value, label]) => (
        <SmallButton
          key={label}
          onClick={() => setValue(value)}
          variant={currentValue === value ? 'primary' : 'secondary'}
        >
          {label}
        </SmallButton>
      ))}
    </ButtonGroup>
  );
}

const buttonsPropType = {
  isRequired: ({ buttons }) => {
    if (!buttons) {
      return new Error(
        `The prop buttons is marked as required in MultiButtonToggle, but its value is '${buttons}'`
      );
    }
    // We expect this data structure to look like:
    // [[value(unrestricted type), label(string)], [value(unrestricted type), label(string)], ...]
    if (
      !Array.isArray(buttons) ||
      buttons.length < 2 ||
      buttons.reduce(
        (prevVal, button) => prevVal || typeof button[1] !== 'string',
        false
      )
    ) {
      return new Error(
        `Invalid prop buttons supplied to MultiButtonToggle. Validation failed.`
      );
    }

    return null;
  },
};

MultiButtonToggle.propTypes = {
  buttons: buttonsPropType.isRequired,
  currentValue: string.isRequired,
  onChange: func.isRequired,
};

export default MultiButtonToggle;
