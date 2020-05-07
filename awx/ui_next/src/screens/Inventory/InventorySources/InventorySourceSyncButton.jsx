import React, { useCallback, useState, useEffect } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { SyncIcon, MinusCircleIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail/ErrorDetail';
import { InventoryUpdatesAPI, InventorySourcesAPI } from '../../../api';

function InventorySourceSyncButton({ onSyncLoading, source, i18n }) {
  const [updateStatus, setUpdateStatus] = useState(source.status);

  const {
    isLoading: startSyncLoading,
    error: startSyncError,
    request: startSyncProcess,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { status },
      } = await InventorySourcesAPI.createSyncStart(source.id);

      setUpdateStatus(status);

      return status;
    }, [source.id]),
    {}
  );

  const {
    isLoading: cancelSyncLoading,
    error: cancelSyncError,
    request: cancelSyncProcess,
  } = useRequest(
    useCallback(async () => {
      const {
        data: {
          summary_fields: {
            current_update: { id },
          },
        },
      } = await InventorySourcesAPI.readDetail(source.id);

      await InventoryUpdatesAPI.createSyncCancel(id);
      setUpdateStatus(null);
    }, [source.id])
  );

  useEffect(() => onSyncLoading(startSyncLoading || cancelSyncLoading), [
    onSyncLoading,
    startSyncLoading,
    cancelSyncLoading,
  ]);

  const { error, dismissError } = useDismissableError(
    cancelSyncError || startSyncError
  );

  return (
    <>
      {updateStatus === 'pending' ? (
        <Tooltip content={i18n._(t`Cancel sync process`)} position="top">
          <Button
            isDisabled={cancelSyncLoading || startSyncLoading}
            aria-label={i18n._(t`Cancel sync source`)}
            variant="plain"
            onClick={cancelSyncProcess}
          >
            <MinusCircleIcon />
          </Button>
        </Tooltip>
      ) : (
        <Tooltip content={i18n._(t`Start sync process`)} position="top">
          <Button
            isDisabled={cancelSyncLoading || startSyncLoading}
            aria-label={i18n._(t`Start sync source`)}
            variant="plain"
            onClick={startSyncProcess}
          >
            <SyncIcon />
          </Button>
        </Tooltip>
      )}
      {error && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {startSyncError
            ? i18n._(t`Failed to sync inventory source.`)
            : i18n._(t`Failed to cancel inventory source sync.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

InventorySourceSyncButton.defaultProps = {
  source: {},
};

InventorySourceSyncButton.propTypes = {
  onSyncLoading: PropTypes.func.isRequired,
  source: PropTypes.shape({}),
};

export default withI18n()(InventorySourceSyncButton);
