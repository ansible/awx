import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { useField } from 'formik';
import { Split, SplitItem } from '@patternfly/react-core';
import { yamlToJson, jsonToYaml, isJson } from '@util/yaml';
import CodeMirrorInput from './CodeMirrorInput';
import YamlJsonToggle from './YamlJsonToggle';
import { JSON_MODE, YAML_MODE } from './constants';

function VariablesField({ id, name, label, readOnly }) {
  const [field, meta, helpers] = useField(name);
  const [mode, setMode] = useState(isJson(field.value) ? JSON_MODE : YAML_MODE);

  return (
    <Field name={name}>
      {({ field, form }) => (
        <div className="pf-c-form__group">
          <Split gutter="sm">
            <SplitItem>
              <label htmlFor={id} className="pf-c-form__label">
                <span className="pf-c-form__label-text">{label}</span>
              </label>
            </SplitItem>
            <SplitItem>
              <YamlJsonToggle
                mode={mode}
                onChange={newMode => {
                  try {
                    const newVal =
                      newMode === YAML_MODE
                        ? jsonToYaml(field.value)
                        : yamlToJson(field.value);
                helpers.setValue(newVal);
                    setMode(newMode);
                  } catch (err) {
                helpers.setError(err.message);
                  }
                }}
              />
            </SplitItem>
          </Split>
          <CodeMirrorInput
            mode={mode}
            readOnly={readOnly}
            {...field}
            onChange={newVal => {
          helpers.setValue(newVal);
            }}
        hasErrors={!!meta.error}
          />
      {meta.error ? (
        <div className="pf-c-form__helper-text pf-m-error" aria-live="polite">
          {meta.error}
            </div>
          ) : null}
        </div>
      )}
    </Field>
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
