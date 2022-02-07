import React, { useState, useEffect, useCallback } from 'react';
import { string, bool, func, oneOf } from 'prop-types';

import { t } from '@lingui/macro';
import { useField } from 'formik';
import styled from 'styled-components';
import { Split, SplitItem, Button, Modal } from '@patternfly/react-core';
import { ExpandArrowsAltIcon } from '@patternfly/react-icons';
import { yamlToJson, jsonToYaml, isJsonString } from 'util/yaml';
import { CheckboxField } from '../FormField';
import MultiButtonToggle from '../MultiButtonToggle';
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
  id,
  name,
  label,
  readOnly,
  promptId,
  tooltip,
  initialMode,
  onModeChange,
}) {
  // track focus manually, because the Code Editor library doesn't wire
  // into Formik completely
  const [shouldValidate, setShouldValidate] = useState(false);
  const [mode, setMode] = useState(initialMode || YAML_MODE);
  const validate = useCallback(
    (value) => {
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

  useEffect(() => {
    if (isJsonString(field.value)) {
      // mode's useState above couldn't be initialized to JSON_MODE because
      // the field value had to be defined below it
      setMode(JSON_MODE);
      onModeChange(JSON_MODE);
      helpers.setValue(JSON.stringify(JSON.parse(field.value), null, 2));
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(
    () => {
      if (shouldValidate) {
        helpers.setError(validate(field.value));
      }
    },
    [shouldValidate, validate] // eslint-disable-line react-hooks/exhaustive-deps
  );
  const [lastYamlValue, setLastYamlValue] = useState(
    mode === YAML_MODE ? field.value : null
  );
  const [isJsonEdited, setIsJsonEdited] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const handleModeChange = (newMode) => {
    if (newMode === YAML_MODE && !isJsonEdited && lastYamlValue !== null) {
      helpers.setValue(lastYamlValue, false);
      setMode(newMode);
      onModeChange(newMode);
      return;
    }

    try {
      const newVal =
        newMode === YAML_MODE
          ? jsonToYaml(field.value)
          : yamlToJson(field.value);
      helpers.setValue(newVal, false);
      setMode(newMode);
      onModeChange(newMode);
    } catch (err) {
      helpers.setError(err.message);
    }
  };

  const handleChange = (newVal) => {
    helpers.setValue(newVal);
    if (mode === JSON_MODE) {
      setIsJsonEdited(true);
    } else {
      setLastYamlValue(newVal);
      setIsJsonEdited(false);
    }
  };

  return (
    <div>
      <VariablesFieldInternals
        id={id}
        name={name}
        label={label}
        readOnly={readOnly}
        promptId={promptId}
        tooltip={tooltip}
        onExpand={() => setIsExpanded(true)}
        mode={mode}
        setMode={handleModeChange}
        setShouldValidate={setShouldValidate}
        handleChange={handleChange}
      />
      <Modal
        variant="xlarge"
        title={label}
        ouiaId={`${id}-modal`}
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
            setMode={handleModeChange}
            setShouldValidate={setShouldValidate}
            handleChange={handleChange}
          />
        </div>
      </Modal>
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
  initialMode: oneOf([YAML_MODE, JSON_MODE]),
  onModeChange: func,
};
VariablesField.defaultProps = {
  readOnly: false,
  promptId: null,
  initialMode: YAML_MODE,
  onModeChange: () => {},
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
  handleChange,
}) {
  const [field, meta, helpers] = useField(name);

  useEffect(() => {
    if (mode === YAML_MODE) {
      return;
    }
    try {
      helpers.setValue(JSON.stringify(JSON.parse(field.value), null, 2));
    } catch (e) {
      helpers.setError(e.message);
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="pf-c-form__group">
      <FieldHeader data-cy={`${id}-label`}>
        <Split hasGutter>
          <SplitItem>
            <label htmlFor={id} className="pf-c-form__label">
              <span className="pf-c-form__label-text">{label}</span>
            </label>
            {tooltip && <Popover content={tooltip} id={`${id}-tooltip`} />}
          </SplitItem>
          <SplitItem>
            <MultiButtonToggle
              buttons={[
                [YAML_MODE, 'YAML'],
                [JSON_MODE, 'JSON'],
              ]}
              value={mode}
              onChange={setMode}
              name={name}
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
            ouiaId={`${id}-expand`}
          >
            <ExpandArrowsAltIcon />
          </Button>
        )}
      </FieldHeader>
      <CodeEditor
        id={id}
        mode={mode}
        readOnly={readOnly}
        {...field}
        onChange={handleChange}
        fullHeight={fullHeight}
        onFocus={() => setShouldValidate(false)}
        onBlur={() => setShouldValidate(true)}
        hasErrors={!!meta.error}
      />
    </div>
  );
}

export default VariablesField;
