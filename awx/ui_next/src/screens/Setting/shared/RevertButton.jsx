import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { Button, Tooltip } from '@patternfly/react-core';
import styled from 'styled-components';

const ButtonWrapper = styled.div`
  margin-left: auto;
  &&& {
    --pf-c-button--FontSize: var(--pf-c-button--m-small--FontSize);
  }
`;

function RevertButton({ i18n, id, defaultValue, isDisabled = false }) {
  const [field, meta, helpers] = useField(id);
  const initialValue = meta.initialValue ?? '';
  const currentValue = field.value;
  let isRevertable = true;
  let isMatch = false;

  if (currentValue === defaultValue && currentValue !== initialValue) {
    isRevertable = false;
  }

  if (currentValue === defaultValue && currentValue === initialValue) {
    isMatch = true;
  }

  function handleConfirm() {
    helpers.setValue(isRevertable ? defaultValue : initialValue);
  }

  const revertTooltipContent = isRevertable
    ? i18n._(t`Revert to factory default.`)
    : i18n._(t`Restore initial value.`);
  const tooltipContent =
    isDisabled || isMatch
      ? i18n._(t`Setting matches factory default.`)
      : revertTooltipContent;

  return (
    <Tooltip entryDelay={700} content={tooltipContent}>
      <ButtonWrapper>
        <Button
          aria-label={isRevertable ? i18n._(t`Revert`) : i18n._(t`Undo`)}
          ouiaId={`${id}-revert`}
          isInline
          isSmall
          onClick={handleConfirm}
          type="button"
          variant="link"
          isDisabled={isDisabled || isMatch}
        >
          {isRevertable ? i18n._(t`Revert`) : i18n._(t`Undo`)}
        </Button>
      </ButtonWrapper>
    </Tooltip>
  );
}

RevertButton.propTypes = {
  id: PropTypes.string.isRequired,
};

export default withI18n()(RevertButton);
