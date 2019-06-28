import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ActionGroup as PFActionGroup, Button } from '@patternfly/react-core';
import styled from 'styled-components';

const ActionGroup = styled(PFActionGroup)`
  display: flex;
  justify-content: flex-end;
  --pf-c-form__group--m-action--MarginTop: 0;

  .pf-c-form__actions {
    display: grid;
    gap: 24px;
    grid-template-columns: auto auto;
    margin: 0;

    & > button {
      margin: 0;
    }
  }
`;

const FormActionGroup = ({ onSubmit, submitDisabled, onCancel, i18n }) => (
  <ActionGroup>
    <Button
      aria-label={i18n._(t`Save`)}
      variant="primary"
      type="submit"
      onClick={onSubmit}
      isDisabled={submitDisabled}
    >
      {i18n._(t`Save`)}
    </Button>
    <Button
      aria-label={i18n._(t`Cancel`)}
      variant="secondary"
      type="button"
      onClick={onCancel}
    >
      {i18n._(t`Cancel`)}
    </Button>
  </ActionGroup>
);

FormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool,
};

FormActionGroup.defaultProps = {
  submitDisabled: false,
};

export default withI18n()(FormActionGroup);
