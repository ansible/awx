import 'styled-components/macro';
import React, { Fragment, useState, useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Switch, Tooltip } from '@patternfly/react-core';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import useRequest from '../../util/useRequest';
import { HostsAPI } from '../../api';

function HostToggle({
  i18n,
  className,
  host,
  isDisabled = false,
  onToggle,
  tooltip = i18n._(
    t`Indicates if a host is available and should be included in running
    jobs.  For hosts that are part of an external inventory, this may be
    reset by the inventory sync process.`
  ),
}) {
  const [isEnabled, setIsEnabled] = useState(host.enabled);
  const [showError, setShowError] = useState(false);

  const { result, isLoading, error, request: toggleHost } = useRequest(
    useCallback(async () => {
      await HostsAPI.update(host.id, {
        enabled: !isEnabled,
      });
      return !isEnabled;
    }, [host, isEnabled]),
    host.enabled
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
    <Fragment>
      <Tooltip content={tooltip} position="top">
        <Switch
          className={className}
          css="display: inline-flex;"
          id={`host-${host.id}-toggle`}
          label={i18n._(t`On`)}
          labelOff={i18n._(t`Off`)}
          isChecked={isEnabled}
          isDisabled={
            isLoading ||
            isDisabled ||
            !host.summary_fields.user_capabilities.edit
          }
          onChange={toggleHost}
          aria-label={i18n._(t`Toggle host`)}
        />
      </Tooltip>
      {showError && error && !isLoading && (
        <AlertModal
          variant="error"
          title={i18n._(t`Error!`)}
          isOpen={error && !isLoading}
          onClose={() => setShowError(false)}
        >
          {i18n._(t`Failed to toggle host.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </Fragment>
  );
}

export default withI18n()(HostToggle);
