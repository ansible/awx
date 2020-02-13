import React from 'react';
import { bool, func, node, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Tooltip } from '@patternfly/react-core';
import { CheckboxField } from '@components/FormField';
import { QuestionCircleIcon as PFQuestionCircleIcon } from '@patternfly/react-icons';
import styled from 'styled-components';

const QuestionCircleIcon = styled(PFQuestionCircleIcon)`
  margin-left: 10px;
`;

const FieldHeader = styled.div`
  display: flex;
  justify-content: space-between;
  padding-bottom: var(--pf-c-form__label--PaddingBottom);

  label {
    --pf-c-form__label--PaddingBottom: 0px;
  }
`;

const StyledCheckboxField = styled(CheckboxField)`
  --pf-c-check__label--FontSize: var(--pf-c-form__label--FontSize);
`;

function FieldWithPrompt({
  children,
  fieldId,
  i18n,
  isRequired,
  label,
  promptId,
  promptName,
  promptValidate,
  tooltip,
  tooltipMaxWidth,
}) {
  return (
    <div className="pf-c-form__group">
      <FieldHeader>
        <div>
          <label className="pf-c-form__label" htmlFor={fieldId}>
            <span className="pf-c-form__label-text">{label}</span>
            {isRequired && (
              <span className="pf-c-form__label-required" aria-hidden="true">
                *
              </span>
            )}
          </label>
          {tooltip && (
            <Tooltip
              content={tooltip}
              maxWidth={tooltipMaxWidth}
              position="right"
            >
              <QuestionCircleIcon />
            </Tooltip>
          )}
        </div>
        <StyledCheckboxField
          id={promptId}
          label={i18n._(t`Prompt On Launch`)}
          name={promptName}
          validate={promptValidate}
        />
      </FieldHeader>
      {children}
    </div>
  );
}

FieldWithPrompt.propTypes = {
  fieldId: string.isRequired,
  isRequired: bool,
  label: string.isRequired,
  promptId: string.isRequired,
  promptName: string.isRequired,
  promptValidate: func,
  tooltip: node,
  tooltipMaxWidth: string,
};

FieldWithPrompt.defaultProps = {
  isRequired: false,
  promptValidate: () => {},
  tooltip: null,
  tooltipMaxWidth: '',
};

export default withI18n()(FieldWithPrompt);
