import React, { useState, useEffect, useCallback } from 'react';

import { t } from '@lingui/macro';
import { Switch, Tooltip } from '@patternfly/react-core';
import useRequest from 'hooks/useRequest';
import { InstancesAPI } from 'api';
import { useConfig } from 'contexts/Config';
import ErrorDetail from '../ErrorDetail';
import AlertModal from '../AlertModal';

function InstancePeerControl({
  className,
  fetchInstances,
  instance,
  onToggle,
}) {
  const { me = {} } = useConfig();
  const [isEnabled, setIsEnabled] = useState(instance.peers_from_control_nodes);
  const [showError, setShowError] = useState(false);

  const {
    result,
    isLoading,
    error,
    request: toggleInstance,
  } = useRequest(
    useCallback(async () => {
      await InstancesAPI.update(instance.id, {
        peers_from_control_nodes: !isEnabled,
      });
      await fetchInstances();
      return !isEnabled;
    }, [instance, isEnabled, fetchInstances]),
    instance.peers_from_control_nodes
  );

  useEffect(() => {
    if (result !== isEnabled) {
      setIsEnabled(result);
      if (onToggle) {
        onToggle(result);
      }
    }
  }, [result, isEnabled, onToggle]);

  useEffect(() => {
    if (error) {
      setShowError(true);
    }
  }, [error]);

  return (
    <>
      <Tooltip
        content={t`Peer the instance to control node. If disabled, instance is not connected to control node.`}
        position="top"
      >
        <Switch
          className={className}
          css="display: inline-flex;"
          id={`host-${instance.id}-peer-toggle`}
          label={t`Peer to control nodes Enabled`}
          labelOff={t`Peer to control nodes Disabled`}
          isChecked={isEnabled}
          isDisabled={isLoading || !me?.is_superuser}
          onChange={toggleInstance}
          ouiaId={`host-${instance.id}-peer-toggle`}
          aria-label={t`Toggle instance`}
        />
      </Tooltip>
      {showError && error && !isLoading && (
        <AlertModal
          variant="error"
          title={t`Error!`}
          isOpen={error && !isLoading}
          onClose={() => setShowError(false)}
        >
          {t`Failed to peer instance.`}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default InstancePeerControl;
