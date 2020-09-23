import React, { useState, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Tooltip } from '@patternfly/react-core';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import useRequest from '../../util/useRequest';
import { InstancesAPI } from '../../api';
import { useConfig } from '../../contexts/Config';

function InstanceToggle({
  className,
  fetchInstances,
  instance,
  onToggle,
  i18n,
}) {
  const { me = {} } = useConfig();
  const [isEnabled, setIsEnabled] = useState(instance.enabled);
  const [showError, setShowError] = useState(false);

  const { result, isLoading, error, request: toggleInstance } = useRequest(
    useCallback(async () => {
      await InstancesAPI.update(instance.id, { enabled: !isEnabled });
      await fetchInstances();
      return !isEnabled;
    }, [instance, isEnabled, fetchInstances]),
    instance.enabled
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
        content={i18n._(
          t`Set the instance online or offline. If offline, jobs will not be assigned to this instance.`
        )}
        position="top"
      >
        <Switch
          className={className}
          css="display: inline-flex;"
          id={`host-${instance.id}-toggle`}
          label={i18n._(t`On`)}
          labelOff={i18n._(t`Off`)}
          isChecked={isEnabled}
          isDisabled={isLoading || !me?.is_superuser}
          onChange={toggleInstance}
          aria-label={i18n._(t`Toggle instance`)}
        />
      </Tooltip>
      {showError && error && !isLoading && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={error && !isLoading}
          onClose={() => setShowError(false)}
        >
          {i18n._(t`Failed to toggle instance.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </>
  );
}

export default withI18n()(InstanceToggle);
