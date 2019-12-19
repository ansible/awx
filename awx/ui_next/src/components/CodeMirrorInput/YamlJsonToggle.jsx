import React from 'react';
import { oneOf, func } from 'prop-types';
import styled from 'styled-components';
import { Button } from '@patternfly/react-core';
import ButtonGroup from '../ButtonGroup';

const SmallButton = styled(Button)`
  padding: 3px 8px;
  font-size: var(--pf-global--FontSize--xs);
`;

const YAML_MODE = 'yaml';
const JSON_MODE = 'javascript';

function YamlJsonToggle({ mode, onChange }) {
  const setMode = newMode => {
    if (mode !== newMode) {
      onChange(newMode);
    }
  };

  return (
    <ButtonGroup>
      <SmallButton
        onClick={() => setMode(YAML_MODE)}
        variant={mode === YAML_MODE ? 'primary' : 'secondary'}
      >
        YAML
      </SmallButton>
      <SmallButton
        onClick={() => setMode(JSON_MODE)}
        variant={mode === JSON_MODE ? 'primary' : 'secondary'}
      >
        JSON
      </SmallButton>
    </ButtonGroup>
  );
}
YamlJsonToggle.propTypes = {
  mode: oneOf([YAML_MODE, JSON_MODE]).isRequired,
  onChange: func.isRequired,
};

export default YamlJsonToggle;
