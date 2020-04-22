import React, { useCallback, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Button, Tooltip } from '@patternfly/react-core';
import { CopyIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '@util/useRequest';
import AlertModal from '@components/AlertModal';
import ErrorDetail from '@components/ErrorDetail';

function CopyButton({ i18n, itemName, copyItem, disableButtons }) {
  const { isLoading, error, request: copyTemplateToAPI } = useRequest(
    useCallback(async () => {
      await copyItem();

      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []),
    {}
  );

  useEffect(() => {
    if (isLoading) {
      return disableButtons(true);
    }
    return disableButtons(false);
  }, [isLoading, disableButtons]);

  const { dismissError } = useDismissableError(error);

  return (
    <>
      <Tooltip content={i18n._(t`Copy Template`)} position="top">
        <Button
          aria-label={i18n._(t`Copy Template`)}
          css="grid-column: 3"
          variant="plain"
          onClick={() => copyTemplateToAPI()}
        >
          <CopyIcon />
        </Button>
      </Tooltip>
      <AlertModal
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => dismissError}
      >
        {i18n._(t`Failed to copy ${itemName}.`)}
        <ErrorDetail error={error} />
      </AlertModal>
    </>
  );
}
export default withI18n()(CopyButton);
