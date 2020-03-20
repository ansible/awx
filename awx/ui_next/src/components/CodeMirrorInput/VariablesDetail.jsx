import React, { useState, useEffect } from 'react';
import { string, node, number } from 'prop-types';
import { Split, SplitItem, TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from '@components/DetailList';
import MultiButtonToggle from '@components/MultiButtonToggle';
import { yamlToJson, jsonToYaml, isJson } from '@util/yaml';
import CodeMirrorInput from './CodeMirrorInput';
import { JSON_MODE, YAML_MODE } from './constants';

function getValueAsMode(value, mode) {
  if (!value) {
    if (mode === JSON_MODE) {
      return '{}';
    }
    return '---';
  }
  const modeMatches = isJson(value) === (mode === JSON_MODE);
  if (modeMatches) {
    return value;
  }
  return mode === YAML_MODE ? jsonToYaml(value) : yamlToJson(value);
}

function VariablesDetail({ value, label, rows, fullHeight }) {
  const [mode, setMode] = useState(isJson(value) ? JSON_MODE : YAML_MODE);
  const [currentValue, setCurrentValue] = useState(value || '---');
  const [error, setError] = useState(null);

  useEffect(() => {
    setCurrentValue(getValueAsMode(value, mode));
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [value]);

  return (
    <>
      <DetailName
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
      >
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
            <MultiButtonToggle
              buttons={[[YAML_MODE, 'YAML'], [JSON_MODE, 'JSON']]}
              value={mode}
              onChange={newMode => {
                try {
                  setCurrentValue(getValueAsMode(currentValue, newMode));
                  setMode(newMode);
                } catch (err) {
                  setError(err);
                }
              }}
            />
          </SplitItem>
        </Split>
      </DetailName>
      <DetailValue
        component={TextListItemVariants.dd}
        fullWidth
        css="grid-column: 1 / -1; margin-top: -20px"
      >
        <CodeMirrorInput
          mode={mode}
          value={currentValue}
          readOnly
          rows={rows}
          fullHeight={fullHeight}
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
      </DetailValue>
    </>
  );
}
VariablesDetail.propTypes = {
  value: string.isRequired,
  label: node.isRequired,
  rows: number,
};
VariablesDetail.defaultProps = {
  rows: null,
};

export default VariablesDetail;
