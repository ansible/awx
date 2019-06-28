import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { Field } from 'formik';
import { Button, Split, SplitItem } from '@patternfly/react-core';
import styled from 'styled-components';
import ButtonGroup from '../ButtonGroup';
import CodeMirrorInput from './CodeMirrorInput';
import { yamlToJson, jsonToYaml } from '../../util/yaml';

const YAML_MODE = 'yaml';
const JSON_MODE = 'javascript';

const SmallButton = styled(Button)`
  padding: 3px 8px;
  font-size: var(--pf-global--FontSize--xs);
`;

function VariablesField({ id, name, label, readOnly }) {
  const [mode, setMode] = useState(YAML_MODE);

  return (
    <Field
      name={name}
      render={({ field, form }) => (
        <div className="pf-c-form__group">
          <Split gutter="sm">
            <SplitItem>
              <label htmlFor={id} className="pf-c-form__label">
                {label}
              </label>
            </SplitItem>
            <SplitItem>
              <ButtonGroup>
                <SmallButton
                  onClick={() => {
                    if (mode === YAML_MODE) {
                      return;
                    }
                    try {
                      form.setFieldValue(name, jsonToYaml(field.value));
                      setMode(YAML_MODE);
                    } catch (err) {
                      form.setFieldError(name, err.message);
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
                      form.setFieldValue(name, yamlToJson(field.value));
                      setMode(JSON_MODE);
                    } catch (err) {
                      form.setFieldError(name, err.message);
                    }
                  }}
                  variant={mode === JSON_MODE ? 'primary' : 'secondary'}
                >
                  JSON
                </SmallButton>
              </ButtonGroup>
            </SplitItem>
          </Split>
          <CodeMirrorInput
            mode={mode}
            readOnly={readOnly}
            {...field}
            onChange={value => {
              form.setFieldValue(name, value);
            }}
            hasErrors={!!form.errors[field.name]}
          />
          {form.errors[field.name] ? (
            <div
              className="pf-c-form__helper-text pf-m-error"
              aria-live="polite"
            >
              {form.errors[field.name]}
            </div>
          ) : null}
        </div>
      )}
    />
  );
}
VariablesField.propTypes = {
  id: string.isRequired,
  name: string.isRequired,
  label: string.isRequired,
  readOnly: bool,
};
VariablesField.defaultProps = {
  readOnly: false,
};

export default VariablesField;
