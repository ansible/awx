import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import useRequest, { useDismissableError } from 'hooks/useRequest';
import AlertModal from 'components/AlertModal/AlertModal';
import ErrorDetail from 'components/ErrorDetail/ErrorDetail';
import { InventoriesAPI } from 'api';

function ConstructedInventorySyncButton({ inventoryId }) {
  const testId = `constructed-inventory-${inventoryId}-sync`;
  const {
    isLoading: startSyncLoading,
    error: startSyncError,
    request: startSyncProcess,
  } = useRequest(
    useCallback(
      async () => InventoriesAPI.syncAllSources(inventoryId),
      [inventoryId]
    ),
    {}
  );

  const { error: startError, dismissError: dismissStartError } =
    useDismissableError(startSyncError);

  return (
    <>
      <Tooltip content={t`Start sync process`} position="top">
        <Button
          ouiaId={testId}
          isDisabled={startSyncLoading}
          aria-label={t`Start inventory source sync`}
          variant="secondary"
          onClick={startSyncProcess}
        >
          {t`Sync`}
        </Button>
      </Tooltip>
      {startError && (
        <AlertModal
          isOpen={startError}
          variant="error"
          title={t`Error!`}
          onClose={dismissStartError}
        >
          {t`Failed to sync constructed inventory source`}
          <ErrorDetail error={startError} />
        </AlertModal>
      )}
    </>
  );
}

ConstructedInventorySyncButton.propTypes = {
  inventoryId: PropTypes.number.isRequired,
};

export default ConstructedInventorySyncButton;
