import 'styled-components/macro';
import React, { useState, useEffect } from 'react';
import { node, number, oneOfType, shape, string, arrayOf } from 'prop-types';
import { Split, SplitItem, TextListItemVariants } from '@patternfly/react-core';
import { DetailName, DetailValue } from '../DetailList';
import MultiButtonToggle from '../MultiButtonToggle';
import Popover from '../Popover';
import {
  yamlToJson,
  jsonToYaml,
  isJsonObject,
  isJsonString,
} from '../../util/yaml';
import CodeMirrorInput from './CodeMirrorInput';
import { JSON_MODE, YAML_MODE } from './constants';

function getValueAsMode(value, mode) {
  if (!value) {
    if (mode === JSON_MODE) {
      return '{}';
    }
    return '---';
  }
  const modeMatches = isJsonString(value) === (mode === JSON_MODE);
  if (modeMatches) {
    return value;
  }
  return mode === YAML_MODE ? jsonToYaml(value) : yamlToJson(value);
}

function VariablesDetail({ dataCy, helpText, value, label, rows, fullHeight }) {
  const [mode, setMode] = useState(
    isJsonObject(value) || isJsonString(value) ? JSON_MODE : YAML_MODE
  );
  const [currentValue, setCurrentValue] = useState(
    isJsonObject(value) ? JSON.stringify(value, null, 2) : value || '---'
  );
  const [error, setError] = useState(null);

  useEffect(() => {
    setCurrentValue(
      getValueAsMode(
        isJsonObject(value) ? JSON.stringify(value, null, 2) : value,
        mode
      )
    );
    /* eslint-disable-next-line react-hooks/exhaustive-deps */
  }, [value]);

  const labelCy = dataCy ? `${dataCy}-label` : null;
  const valueCy = dataCy ? `${dataCy}-value` : null;

  return (
    <>
      <DetailName
        data-cy={labelCy}
        id={dataCy}
        component={TextListItemVariants.dt}
        fullWidth
        css="grid-column: 1 / -1"
      >
        <Split hasGutter>
          <SplitItem>
            <div className="pf-c-form__label">
              <span
                className="pf-c-form__label-text"
                css="font-weight: var(--pf-global--FontWeight--bold)"
              >
                {label}
              </span>
              {helpText && (
                <Popover header={label} content={helpText} id={dataCy} />
              )}
            </div>
          </SplitItem>
          <SplitItem>
            <MultiButtonToggle
              buttons={[
                [YAML_MODE, 'YAML'],
                [JSON_MODE, 'JSON'],
              ]}
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
        data-cy={valueCy}
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
  value: oneOfType([shape({}), arrayOf(string), string]).isRequired,
  label: node.isRequired,
  rows: number,
  dataCy: string,
  helpText: string,
};
VariablesDetail.defaultProps = {
  rows: null,
  dataCy: '',
  helpText: '',
};

export default VariablesDetail;
