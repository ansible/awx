import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import styled from 'styled-components';
import { Split, SplitItem } from '@patternfly/react-core';
import { CheckboxField, FieldTooltip } from '@components/FormField';
import MultiButtonToggle from '@components/MultiButtonToggle';
import { yamlToJson, jsonToYaml, isJson } from '@util/yaml';
import CodeMirrorInput from './CodeMirrorInput';
import { JSON_MODE, YAML_MODE } from './constants';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
`;

const StyledCheckboxField = styled(CheckboxField)`
  --pf-c-check__label--FontSize: var(--pf-c-form__label--FontSize);
`;

function VariablesField({
  i18n,
  id,
  name,
  label,
  readOnly,
  promptId,
  tooltip,
}) {
  const [field, meta, helpers] = useField(name);
  const [mode, setMode] = useState(isJson(field.value) ? JSON_MODE : YAML_MODE);

  return (
    <div className="pf-c-form__group">
      <FieldHeader>
        <Split gutter="sm">
          <SplitItem>
            <label htmlFor={id} className="pf-c-form__label">
              <span className="pf-c-form__label-text">{label}</span>
            </label>
            {tooltip && <FieldTooltip content={tooltip} />}
          </SplitItem>
          <SplitItem>
            <MultiButtonToggle
              buttons={[[YAML_MODE, 'YAML'], [JSON_MODE, 'JSON']]}
              value={mode}
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
        {promptId && (
          <StyledCheckboxField
            id="template-ask-variables-on-launch"
            label={i18n._(t`Prompt On Launch`)}
            name="ask_variables_on_launch"
          />
        )}
      </FieldHeader>
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
  );
}
VariablesField.propTypes = {
  id: string.isRequired,
  name: string.isRequired,
  label: string.isRequired,
  readOnly: bool,
  promptId: string,
};
VariablesField.defaultProps = {
  readOnly: false,
  promptId: null,
};

export default withI18n()(VariablesField);
