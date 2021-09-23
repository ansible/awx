import React from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { ActionGroup, Button } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../FormLayout';

const FormActionGroup = ({ onCancel, onSubmit, submitDisabled }) => (
  <FormFullWidthLayout>
    <ActionGroup>
      <Button
        ouiaId="form-save-button"
        aria-label={t`Save`}
        variant="primary"
        type="button"
        onClick={onSubmit}
        isDisabled={submitDisabled}
      >
        {t`Save`}
      </Button>
      <Button
        ouiaId="form-cancel-button"
        aria-label={t`Cancel`}
        variant="link"
        type="button"
        onMouseDown={(e) => e.preventDefault()}
        onClick={onCancel}
      >
        {t`Cancel`}
      </Button>
    </ActionGroup>
  </FormFullWidthLayout>
);

FormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool,
};

FormActionGroup.defaultProps = {
  submitDisabled: false,
};

export default FormActionGroup;
