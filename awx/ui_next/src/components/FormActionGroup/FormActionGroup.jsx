import React from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ActionGroup, Button } from '@patternfly/react-core';
import { FormFullWidthLayout } from '../FormLayout';

const FormActionGroup = ({
  onCancel,
  onRevert,
  onSubmit,
  submitDisabled,
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
          isDisabled={submitDisabled}
        >
          {i18n._(t`Save`)}
        </Button>
        {onRevert && (
          <Button
            aria-label={i18n._(t`Revert`)}
            variant="secondary"
            type="button"
            onClick={onRevert}
          >
            {i18n._(t`Revert`)}
          </Button>
        )}
        <Button
          aria-label={i18n._(t`Cancel`)}
          variant="secondary"
          type="button"
          onClick={onCancel}
        >
          {i18n._(t`Cancel`)}
        </Button>
      </ActionGroup>
    </FormFullWidthLayout>
  );
};

FormActionGroup.propTypes = {
  onCancel: PropTypes.func.isRequired,
  onRevert: PropTypes.func,
  onSubmit: PropTypes.func.isRequired,
  submitDisabled: PropTypes.bool,
};

FormActionGroup.defaultProps = {
  onRevert: null,
  submitDisabled: false,
};

export default withI18n()(FormActionGroup);
