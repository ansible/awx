import React, { useState } from 'react';
import { string, func, bool, number } from 'prop-types';
import { Split, SplitItem } from '@patternfly/react-core';
import styled from 'styled-components';
import { yamlToJson, jsonToYaml, isJsonString } from '../../util/yaml';
import MultiButtonToggle from '../MultiButtonToggle';
import CodeMirrorInput from './CodeMirrorInput';
import { JSON_MODE, YAML_MODE } from './constants';

function formatJson(jsonString) {
  return JSON.stringify(JSON.parse(jsonString), null, 2);
}

const SplitItemRight = styled(SplitItem)`
  margin-bottom: 5px;
`;

function VariablesInput(props) {
  const { id, label, readOnly, rows, error, onError, className } = props;
  /* eslint-disable react/destructuring-assignment */
  const defaultValue = isJsonString(props.value)
    ? formatJson(props.value)
    : props.value;
  const [value, setValue] = useState(defaultValue);
  const [mode, setMode] = useState(isJsonString(value) ? JSON_MODE : YAML_MODE);
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
      <Split hasGutter>
        <SplitItem>
          <label htmlFor={id} className="pf-c-form__label">
            {label}
          </label>
        </SplitItem>
        <SplitItemRight>
          <MultiButtonToggle
            buttons={[
              [YAML_MODE, 'YAML'],
              [JSON_MODE, 'JSON'],
            ]}
            value={mode}
            onChange={newMode => {
              try {
                if (mode === JSON_MODE) {
                  onChange(jsonToYaml(value));
                } else {
                  onChange(yamlToJson(value));
                }
                setMode(newMode);
              } catch (err) {
                onError(err.message);
              }
            }}
          />
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
