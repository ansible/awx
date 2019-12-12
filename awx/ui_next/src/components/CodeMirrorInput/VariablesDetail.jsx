import React, { useState } from 'react';
import { string, number } from 'prop-types';
import { Split, SplitItem } from '@patternfly/react-core';
import CodeMirrorInput from './CodeMirrorInput';
import YamlJsonToggle from './YamlJsonToggle';
import { yamlToJson, jsonToYaml, isJson } from '../../util/yaml';

const YAML_MODE = 'yaml';
const JSON_MODE = 'javascript';

function VariablesDetail({ value, label, rows }) {
  const [mode, setMode] = useState(isJson(value) ? JSON_MODE : YAML_MODE);
  const [val, setVal] = useState(value);
  const [error, setError] = useState(null);

  return (
    <div css="margin: 20px 0">
      <Split gutter="sm">
        <SplitItem>
          <div className="pf-c-form__label">
            <span
              className="pf-c-form__label-text"
              css="font-weight: var(--pf-global--FontWeight--bold)"
            >
              {label}
            </span>
          </div>
        </SplitItem>
        <SplitItem>
          <YamlJsonToggle
            mode={mode}
            onChange={newMode => {
              try {
                const newVal =
                  newMode === YAML_MODE ? jsonToYaml(val) : yamlToJson(val);
                setVal(newVal);
                setMode(newMode);
              } catch (err) {
                setError(err);
              }
            }}
          />
        </SplitItem>
      </Split>
      <CodeMirrorInput
        mode={mode}
        value={val}
        readOnly
        rows={rows}
        css="margin-top: 10px"
      />
      {error && (
        <div
          css="color: var(--pf-global--danger-color--100);
            font-size: var(--pf-global--FontSize--sm"
        >
          Error: {error.message}
        </div>
      )}
    </div>
  );
}
VariablesDetail.propTypes = {
  value: string.isRequired,
  label: string.isRequired,
  rows: number,
};
VariablesDetail.defaultProps = {
  rows: null,
};

export default VariablesDetail;
