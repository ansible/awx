import React from 'react';
import { func, string } from 'prop-types';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';
import ButtonGroup from './ButtonGroup';

const SmallButton = styled(Button)`
  padding: 3px 8px;
  font-size: var(--pf-global--FontSize--xs);
`;

function Toggle({
  leftLabel,
  leftMode,
  rightLabel,
  rightMode,
  currentMode,
  onChange,
}) {
  const setValue = newValue => {
    if (currentMode !== newValue) {
      onChange(newValue);
    }
  };

  return (
    <ButtonGroup>
      <SmallButton
        onClick={() => setValue(leftMode)}
        variant={currentMode === leftMode ? 'primary' : 'secondary'}
      >
        {leftLabel}
      </SmallButton>
      <SmallButton
        onClick={() => setValue(rightMode)}
        variant={currentMode === rightMode ? 'primary' : 'secondary'}
      >
        {rightLabel}
      </SmallButton>
    </ButtonGroup>
  );
}
Toggle.propTypes = {
  leftLabel: string.isRequired,
  leftMode: string.isRequired,
  rightLabel: string.isRequired,
  rightMode: string.isRequired,
  currentMode: string.isRequired,
  onChange: func.isRequired,
};

export default Toggle;
