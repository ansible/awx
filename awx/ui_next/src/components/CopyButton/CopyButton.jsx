import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Button, Tooltip } from '@patternfly/react-core';
import { CopyIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '@util/useRequest';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';

function CopyButton({ i18n, copyItem, onLoading, onDoneLoading, helperText }) {
  const { isLoading, error: copyError, request: copyItemToAPI } = useRequest(
    copyItem
  );

  useEffect(() => {
    if (isLoading) {
      return onLoading();
    }
    return onDoneLoading();
  }, [isLoading, onLoading, onDoneLoading]);

  const { error, dismissError } = useDismissableError(copyError);

  return (
    <>
      <Tooltip content={helperText.tooltip} position="top">
        <Button
          aria-label={i18n._(t`Copy`)}
          variant="plain"
          onClick={copyItemToAPI}
        >
          <CopyIcon />
        </Button>
      </Tooltip>
      <AlertModal
        aria-label={i18n._(t`Copy Error`)}
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={dismissError}
      >
        {helperText.errorMessage}
        <ErrorDetail error={error} />
      </AlertModal>
    </>
  );
}

CopyButton.propTypes = {
  copyItem: PropTypes.func.isRequired,
  onLoading: PropTypes.func.isRequired,
  onDoneLoading: PropTypes.func.isRequired,
  helperText: PropTypes.shape({
    tooltip: PropTypes.string.isRequired,
    errorMessage: PropTypes.string.isRequired,
  }).isRequired,
};
export default withI18n()(CopyButton);
