import React from 'react';
import { bool, node, string } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { CheckboxField, FieldTooltip } from '@components/FormField';
import styled from 'styled-components';

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
  tooltip,
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
          {tooltip && <FieldTooltip content={tooltip} />}
        </div>
        <StyledCheckboxField
          id={promptId}
          label={i18n._(t`Prompt On Launch`)}
          name={promptName}
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
  tooltip: node,
};

FieldWithPrompt.defaultProps = {
  isRequired: false,
  tooltip: null,
};

export default withI18n()(FieldWithPrompt);
