import React, { useState } from 'react';
import { string, func, bool, number } from 'prop-types';
import { Button, Split, SplitItem } from '@patternfly/react-core';
import styled from 'styled-components';
import ButtonGroup from '@components/ButtonGroup';
import { yamlToJson, jsonToYaml, isJson } from '@util/yaml';
import CodeMirrorInput from './CodeMirrorInput';

const YAML_MODE = 'yaml';
const JSON_MODE = 'javascript';

function formatJson(jsonString) {
  return JSON.stringify(JSON.parse(jsonString), null, 2);
}

const SmallButton = styled(Button)`
  padding: 3px 8px;
  font-size: var(--pf-global--FontSize--xs);
`;

const SplitItemRight = styled(SplitItem)`
  margin-bottom: 5px;
`;

function VariablesInput(props) {
  const { id, label, readOnly, rows, error, onError, className } = props;
  /* eslint-disable react/destructuring-assignment */
  const defaultValue = isJson(props.value)
    ? formatJson(props.value)
    : props.value;
  const [value, setValue] = useState(defaultValue);
  const [mode, setMode] = useState(isJson(value) ? JSON_MODE : YAML_MODE);
  const isControlled = !!props.onChange;
  /* eslint-enable react/destructuring-assignment */

  const onChange = newValue => {
    if (isControlled) {
      props.onChange(newValue);
    }
    setValue(newValue);
  };

  return (
    <div className={`pf-c-form__group ${className || ''}`}>
      <Split gutter="sm">
        <SplitItem>
          <label htmlFor={id} className="pf-c-form__label">
            {label}
          </label>
        </SplitItem>
        <SplitItemRight>
          <ButtonGroup>
            <SmallButton
              onClick={() => {
                if (mode === YAML_MODE) {
                  return;
                }
                try {
                  onChange(jsonToYaml(value));
                  setMode(YAML_MODE);
                } catch (err) {
                  onError(err.message);
                }
              }}
              variant={mode === YAML_MODE ? 'primary' : 'secondary'}
            >
              YAML
            </SmallButton>
            <SmallButton
              onClick={() => {
                if (mode === JSON_MODE) {
                  return;
                }
                try {
                  onChange(yamlToJson(value));
                  setMode(JSON_MODE);
                } catch (err) {
                  onError(err.message);
                }
              }}
              variant={mode === JSON_MODE ? 'primary' : 'secondary'}
            >
              JSON
            </SmallButton>
          </ButtonGroup>
        </SplitItemRight>
      </Split>
      <CodeMirrorInput
        mode={mode}
        readOnly={readOnly}
        value={value}
        onChange={onChange}
        rows={rows}
        hasErrors={!!error}
      />
      {error ? (
        <div className="pf-c-form__helper-text pf-m-error" aria-live="polite">
          {error}
        </div>
      ) : null}
    </div>
  );
}
VariablesInput.propTypes = {
  id: string.isRequired,
  label: string.isRequired,
  value: string.isRequired,
  readOnly: bool,
  error: string,
  rows: number,
  onChange: func,
  onError: func,
};
VariablesInput.defaultProps = {
  readOnly: false,
  onChange: null,
  rows: 6,
  error: null,
  onError: () => {},
};

export default styled(VariablesInput)`
  --pf-c-form__label--FontSize: var(--pf-global--FontSize--sm);
`;
