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
    <>
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
    </>
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


/*
import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Field, useFormikContext } from 'formik';
import { Split, SplitItem } from '@patternfly/react-core';
import { yamlToJson, jsonToYaml, isJson } from '@util/yaml';
import { CheckboxField } from '@components/FormField';
import styled from 'styled-components';
import CodeMirrorInput from './CodeMirrorInput';
import YamlJsonToggle from './YamlJsonToggle';
import { JSON_MODE, YAML_MODE } from './constants';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
`;

const StyledCheckboxField = styled(CheckboxField)`
  --pf-c-check__label--FontSize: var(--pf-c-form__label--FontSize);
`;

function VariablesField({ i18n, id, name, label, readOnly, promptId }) {
  const { values, setFieldError, setFieldValue } = useFormikContext();
  const value = values[name];
  const [mode, setMode] = useState(isJson(value) ? JSON_MODE : YAML_MODE);

  return (
    <div className="pf-c-form__group">
      <FieldHeader>
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
                      ? jsonToYaml(value)
                      : yamlToJson(value);
                  setFieldValue(name, newVal);
                  setMode(newMode);
                } catch (err) {
                  setFieldError(name, err.message);
                }
              }}
            />
          </SplitItem>
        </Split>
        {promptId && (
          <StyledCheckboxField
            id="template-ask-variables-on-launch"
            label={i18n._(t`Prompt On Launch`)}
            name="ask_variables_on_launch"
          />
        )}
      </FieldHeader>
      <Field name={name}>
        {({ field, form }) => (
          <>
            <CodeMirrorInput
              mode={mode}
              readOnly={readOnly}
              {...field}
              onChange={newVal => {
                form.setFieldValue(name, newVal);
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
          </>
        )}
      </Field>
    </div>
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

export default withI18n()(VariablesField);
*/
