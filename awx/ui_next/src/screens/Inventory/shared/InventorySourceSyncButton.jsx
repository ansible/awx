import React, { useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, Tooltip } from '@patternfly/react-core';
import { SyncIcon, MinusCircleIcon } from '@patternfly/react-icons';
import useRequest, { useDismissableError } from '../../../util/useRequest';
import AlertModal from '../../../components/AlertModal/AlertModal';
import ErrorDetail from '../../../components/ErrorDetail/ErrorDetail';
import { InventoryUpdatesAPI, InventorySourcesAPI } from '../../../api';

function InventorySourceSyncButton({ source, icon, i18n }) {
  const {
    isLoading: startSyncLoading,
    error: startSyncError,
    request: startSyncProcess,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { status },
      } = await InventorySourcesAPI.createSyncStart(source.id);

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
    }, [source.id])
  );

  const {
    error: startError,
    dismissError: dismissStartError,
  } = useDismissableError(startSyncError);
  const {
    error: cancelError,
    dismissError: dismissCancelError,
  } = useDismissableError(cancelSyncError);

  return (
    <>
      {['running', 'pending', 'updating'].includes(source.status) ? (
        <Tooltip content={i18n._(t`Cancel sync process`)} position="top">
          <Button
            isDisabled={cancelSyncLoading || startSyncLoading}
            aria-label={i18n._(t`Cancel sync source`)}
            variant={icon ? 'plain' : 'secondary'}
            onClick={cancelSyncProcess}
          >
            {icon ? <MinusCircleIcon /> : i18n._(t`Cancel sync`)}
          </Button>
        </Tooltip>
      ) : (
        <Tooltip content={i18n._(t`Start sync process`)} position="top">
          <Button
            isDisabled={cancelSyncLoading || startSyncLoading}
            aria-label={i18n._(t`Start sync source`)}
            variant={icon ? 'plain' : 'secondary'}
            onClick={startSyncProcess}
          >
            {icon ? <SyncIcon /> : i18n._(t`Sync`)}
          </Button>
        </Tooltip>
      )}
      {startError && (
        <AlertModal
          isOpen={startError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissStartError}
        >
          {i18n._(t`Failed to sync inventory source.`)}
          <ErrorDetail error={startError} />
        </AlertModal>
      )}
      {cancelError && (
        <AlertModal
          isOpen={cancelError}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissCancelError}
        >
          {i18n._(t`Failed to cancel inventory source sync.`)}
          <ErrorDetail error={cancelError} />
        </AlertModal>
      )}
    </>
  );
}

InventorySourceSyncButton.defaultProps = {
  source: {},
  icon: true,
};

InventorySourceSyncButton.propTypes = {
  source: PropTypes.shape({}),
  icon: PropTypes.bool,
};

export default withI18n()(InventorySourceSyncButton);
