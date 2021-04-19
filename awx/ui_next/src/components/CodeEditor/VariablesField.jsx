import React, { useState, useEffect, useCallback } from 'react';
import { string, bool } from 'prop-types';

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

function VariablesField({ id, name, label, readOnly, promptId, tooltip }) {
  // track focus manually, because the Code Editor library doesn't wire
  // into Formik completely
  const [shouldValidate, setShouldValidate] = useState(false);
  const [mode, setMode] = useState(YAML_MODE);
  const validate = useCallback(
    value => {
      if (!shouldValidate) {
        return undefined;
      }
      try {
        if (mode === YAML_MODE) {
          yamlToJson(value);
        } else {
          JSON.parse(value);
        }
      } catch (error) {
        return error.message;
      }
      return undefined;
    },
    [shouldValidate, mode]
  );
  const [field, meta, helpers] = useField({ name, validate });

  // mode's useState above couldn't be initialized to JSON_MODE because
  // the field value had to be defined below it
  useEffect(function initializeMode() {
    if (isJsonString(field.value)) {
      setMode(JSON_MODE);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(
    function validateOnBlur() {
      if (shouldValidate) {
        helpers.setError(validate(field.value));
      }
    },
    [shouldValidate, validate] // eslint-disable-line react-hooks/exhaustive-deps
  );
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <>
      <VariablesFieldInternals
        id={id}
        name={name}
        label={label}
        readOnly={readOnly}
        promptId={promptId}
        tooltip={tooltip}
        onExpand={() => setIsExpanded(true)}
        mode={mode}
        setMode={setMode}
        setShouldValidate={setShouldValidate}
      />
      <Modal
        variant="xlarge"
        title={label}
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        actions={[
          <Button
            aria-label={t`Done`}
            key="select"
            variant="primary"
            onClick={() => setIsExpanded(false)}
            ouiaId={`${id}-variables-unexpand`}
          >
            {t`Done`}
          </Button>,
        ]}
      >
        <div className="pf-c-form">
          <VariablesFieldInternals
            id={`${id}-expanded`}
            name={name}
            label={label}
            readOnly={readOnly}
            promptId={promptId}
            tooltip={tooltip}
            fullHeight
            mode={mode}
            setMode={setMode}
            setShouldValidate={setShouldValidate}
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
  setShouldValidate,
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
            label={t`Prompt on launch`}
            name="ask_variables_on_launch"
          />
        )}
        {onExpand && (
          <Button
            variant="plain"
            aria-label={t`Expand input`}
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
        onFocus={() => setShouldValidate(false)}
        onBlur={() => setShouldValidate(true)}
        hasErrors={!!meta.error}
      />
    </div>
  );
}

export default VariablesField;
