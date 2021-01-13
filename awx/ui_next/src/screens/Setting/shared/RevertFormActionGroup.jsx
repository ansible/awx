import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ActionGroup, Button } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../../../components/FormLayout';

const RevertFormActionGroup = ({
  children,
  onCancel,
  onRevert,
  onSubmit,
  i18n,
}) => {
  return (
    <FormFullWidthLayout>
      <ActionGroup>
        <Button
          aria-label={i18n._(t`Save`)}
          variant="primary"
          type="button"
          onClick={onSubmit}
          ouiaId="save-button"
        >
          {i18n._(t`Save`)}
        </Button>
        <Button
          aria-label={i18n._(t`Revert all to default`)}
          variant="secondary"
          type="button"
          onClick={onRevert}
          ouiaId="revert-all-button"
        >
          {i18n._(t`Revert all to default`)}
        </Button>
        {children}
        <Button
          aria-label={i18n._(t`Cancel`)}
          variant="secondary"
          type="button"
          onClick={onCancel}
          ouiaId="cancel-button"
        >
          {i18n._(t`Cancel`)}
        </Button>
      </ActionGroup>
    </FormFullWidthLayout>
  );
};

RevertFormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onRevert: PropTypes.func.isRequired,
  onSubmit: PropTypes.func.isRequired,
};

export default withI18n()(RevertFormActionGroup);
