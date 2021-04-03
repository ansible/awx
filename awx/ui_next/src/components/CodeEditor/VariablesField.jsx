import React, { useState } from 'react';
import { string, bool } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import styled from 'styled-components';
import { Split, SplitItem, Button, Modal } from '@patternfly/react-core';
import { ExpandArrowsAltIcon } from '@patternfly/react-icons';
import { CheckboxField } from '../FormField';
import MultiButtonToggle from '../MultiButtonToggle';
import { yamlToJson, jsonToYaml, isJsonString } from '../../util/yaml';
import CodeEditor from './CodeEditor';
import Popover from '../Popover';
import { JSON_MODE, YAML_MODE } from './constants';

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: var(--pf-c-form__group-label--PaddingBottom);
`;

const StyledCheckboxField = styled(CheckboxField)`
  --pf-c-check__label--FontSize: var(--pf-c-form__label--FontSize);
  margin-left: auto;
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
  const [field, meta] = useField(name);
  const [mode, setMode] = useState(
    isJsonString(field.value) ? JSON_MODE : YAML_MODE
  );
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      <VariablesFieldInternals
        i18n={i18n}
        id={id}
        name={name}
        label={label}
        readOnly={readOnly}
        promptId={promptId}
        tooltip={tooltip}
        onExpand={() => setIsExpanded(true)}
        mode={mode}
        setMode={setMode}
      />
      <Modal
        variant="xlarge"
        title={label}
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        actions={[
          <Button
            aria-label={i18n._(t`Done`)}
            key="select"
            variant="primary"
            onClick={() => setIsExpanded(false)}
            ouiaId={`${id}-variables-unexpand`}
          >
            {i18n._(t`Done`)}
          </Button>,
        ]}
      >
        <div className="pf-c-form">
          <VariablesFieldInternals
            i18n={i18n}
            id={`${id}-expanded`}
            name={name}
            label={label}
            readOnly={readOnly}
            promptId={promptId}
            tooltip={tooltip}
            fullHeight
            mode={mode}
            setMode={setMode}
          />
        </div>
      </Modal>
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
  promptId: string,
};
VariablesField.defaultProps = {
  readOnly: false,
  promptId: null,
};

function VariablesFieldInternals({
  i18n,
  id,
  name,
  label,
  readOnly,
  promptId,
  tooltip,
  fullHeight,
  mode,
  setMode,
  onExpand,
}) {
  const [field, meta, helpers] = useField(name);

  return (
    <div className="pf-c-form__group">
      <FieldHeader>
        <Split hasGutter>
          <SplitItem>
            <label htmlFor={id} className="pf-c-form__label">
              <span className="pf-c-form__label-text">{label}</span>
            </label>
            {tooltip && <Popover content={tooltip} id={id} />}
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
            label={i18n._(t`Prompt on launch`)}
            name="ask_variables_on_launch"
          />
        )}
        {onExpand && (
          <Button
            variant="plain"
            aria-label={i18n._(t`Expand input`)}
            onClick={onExpand}
            ouiaId={`${id}-variables-expand`}
          >
            <ExpandArrowsAltIcon />
          </Button>
        )}
      </FieldHeader>
      <CodeEditor
        mode={mode}
        readOnly={readOnly}
        {...field}
        onChange={newVal => {
          helpers.setValue(newVal);
        }}
        fullHeight={fullHeight}
        hasErrors={!!meta.error}
      />
    </div>
  );
}

export default withI18n()(VariablesField);
