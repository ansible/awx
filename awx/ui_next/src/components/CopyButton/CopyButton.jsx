import React, { useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import { Button } from '@patternfly/react-core';
import { CopyIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '../../util/useRequest';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';

function CopyButton({
  id,
  copyItem,
  isDisabled,
  onCopyStart,
  onCopyFinish,
  errorMessage,
  i18n,
}) {
  const { isLoading, error: copyError, request: copyItemToAPI } = useRequest(
    copyItem
  );

  useEffect(() => {
    if (isLoading) {
      return onCopyStart();
    }
    return onCopyFinish();
  }, [isLoading, onCopyStart, onCopyFinish]);

  const { error, dismissError } = useDismissableError(copyError);

  return (
    <>
      <Button
        id={id}
        isDisabled={isLoading || isDisabled}
        aria-label={i18n._(t`Copy`)}
        variant="plain"
        onClick={copyItemToAPI}
      >
        <CopyIcon />
      </Button>
      <AlertModal
        aria-label={i18n._(t`Copy Error`)}
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={dismissError}
      >
        {errorMessage}
        <ErrorDetail error={error} />
      </AlertModal>
    </>
  );
}

CopyButton.propTypes = {
  copyItem: PropTypes.func.isRequired,
  onCopyStart: PropTypes.func.isRequired,
  onCopyFinish: PropTypes.func.isRequired,
  errorMessage: PropTypes.string.isRequired,
  isDisabled: PropTypes.bool,
};

CopyButton.defaultProps = {
  isDisabled: false,
};

export default withI18n()(CopyButton);
