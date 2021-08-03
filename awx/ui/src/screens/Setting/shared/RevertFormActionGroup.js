import React from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { ActionGroup, Button } from '@patternfly/react-core';
import { FormFullWidthLayout } from 'components/FormLayout';

const RevertFormActionGroup = ({ children, onCancel, onRevert, onSubmit }) => (
  <FormFullWidthLayout>
    <ActionGroup>
      <Button
        aria-label={t`Save`}
        variant="primary"
        type="button"
        onClick={onSubmit}
        ouiaId="save-button"
      >
        {t`Save`}
      </Button>
      <Button
        aria-label={t`Revert all to default`}
        variant="secondary"
        type="button"
        onClick={onRevert}
        ouiaId="revert-all-button"
      >
        {t`Revert all to default`}
      </Button>
      {children}
      <Button
        aria-label={t`Cancel`}
        variant="link"
        type="button"
        onClick={onCancel}
        ouiaId="cancel-button"
      >
        {t`Cancel`}
      </Button>
    </ActionGroup>
  </FormFullWidthLayout>
);

RevertFormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onRevert: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default RevertFormActionGroup;
