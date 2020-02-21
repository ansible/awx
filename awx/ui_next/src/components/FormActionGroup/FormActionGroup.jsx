import React from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ActionGroup as PFActionGroup, Button } from '@patternfly/react-core';

const ActionGroup = styled(PFActionGroup)`
  display: flex;
  justify-content: flex-end;
  --pf-c-form__group--m-action--MarginTop: 0;
  grid-column: 1 / -1;
  margin-right: calc(var(--pf-c-form__actions--MarginRight) * -1);

  .pf-c-form__actions {
    & > button {
      margin: 0;
    }

    & > :not(:first-child) {
      margin-left: 24px;
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
