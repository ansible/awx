import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { Field } from 'formik';
import { Split, SplitItem } from '@patternfly/react-core';
import CodeMirrorInput from './CodeMirrorInput';
import YamlJsonToggle from './YamlJsonToggle';
import { yamlToJson, jsonToYaml } from '../../util/yaml';

const YAML_MODE = 'yaml';

function VariablesField({ id, name, label, readOnly }) {
  // TODO: detect initial mode
  const [mode, setMode] = useState(YAML_MODE);

  return (
    <Field
      name={name}
      render={({ field, form }) => (
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
                    form.setFieldValue(name, newVal);
                    setMode(newMode);
                  } catch (err) {
                    form.setFieldError(name, err.message);
                  }
                }}
              />
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
