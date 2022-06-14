import React, { useCallback, useEffect, useState, useContext } from 'react';
import { useHistory, useParams } from 'react-router-dom';

import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, DropdownItem, Tooltip } from '@patternfly/react-core';

import useRequest, { useDismissableError } from 'hooks/useRequest';
import { InventoriesAPI, CredentialTypesAPI } from 'api';

import { KebabifiedContext } from 'contexts/Kebabified';
import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import AdHocCommandsWizard from './AdHocCommandsWizard';
import ContentError from '../ContentError';

import { VERBOSE_OPTIONS } from '../../constants';

function AdHocCommands({
  adHocItems,
  hasListItems,
  onLaunchLoading,
  moduleOptions,
}) {
  const history = useHistory();
  const { id } = useParams();

  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);

  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isWizardOpen);
    }
  }, [isKebabified, isWizardOpen, onKebabModalChange]);

  const {
    result: { credentialTypeId, organizationId },
    request: fetchData,
    error: fetchError,
  } = useRequest(
    useCallback(async () => {
      const [{ data }, cred] = await Promise.all([
        InventoriesAPI.readDetail(id),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
      ]);
      return {
        credentialTypeId: cred.data.results[0].id,
        organizationId: data.organization,
      };
    }, [id]),
    { organizationId: null }
  );
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const {
    isLoading: isLaunchLoading,
    error: launchError,
    request: launchAdHocCommands,
  } = useRequest(
    useCallback(
      async (values) => {
        const { data } = await InventoriesAPI.launchAdHocCommands(id, values);
        history.push(`/jobs/command/${data.id}/output`);
      },

      [id, history]
    )
  );

  const { error, dismissError } = useDismissableError(
    launchError || fetchError
  );

  const handleSubmit = async (values) => {
    const {
      credentials,
      credential_passwords: { become_password, ssh_password, ssh_key_unlock },
      execution_environment,
      ...remainingValues
    } = values;
    const newCredential = credentials[0].id;

    const manipulatedValues = {
      credential: newCredential,
      become_password,
      ssh_password,
      ssh_key_unlock,
      execution_environment: execution_environment[0]?.id,
      ...remainingValues,
    };
    await launchAdHocCommands(manipulatedValues);
  };
  useEffect(
    () => onLaunchLoading(isLaunchLoading),
    [isLaunchLoading, onLaunchLoading]
  );

  if (error && isWizardOpen) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={t`Error!`}
        onClose={() => {
          dismissError();
          setIsWizardOpen(false);
        }}
      >
        {launchError ? (
          <>
            {t`Failed to launch job.`}
            <ErrorDetail error={error} />
          </>
        ) : (
          <ContentError error={error} />
        )}
      </AlertModal>
    );
  }
  return (
    // render buttons for drop down and for toolbar
    // if modal is open render the modal
    <>
      <Tooltip content={t`Run ad hoc command`}>
        {isKebabified ? (
          <DropdownItem
            key="cancel-job"
            isDisabled={!hasListItems}
            component="button"
            aria-label={t`Run Command`}
            onClick={() => setIsWizardOpen(true)}
            ouiaId="run-command-dropdown-item"
          >
            {t`Run Command`}
          </DropdownItem>
        ) : (
          <Button
            ouiaId="run-command-button"
            variant="secondary"
            aria-label={t`Run Command`}
            onClick={() => setIsWizardOpen(true)}
            isDisabled={!hasListItems}
          >
            {t`Run Command`}
          </Button>
        )}
      </Tooltip>

      {isWizardOpen && (
        <AdHocCommandsWizard
          adHocItems={adHocItems}
          organizationId={organizationId}
          moduleOptions={moduleOptions}
          verbosityOptions={VERBOSE_OPTIONS}
          credentialTypeId={credentialTypeId}
          onCloseWizard={() => setIsWizardOpen(false)}
          onLaunch={handleSubmit}
          onDismissError={() => dismissError()}
        />
      )}
    </>
  );
}

AdHocCommands.propTypes = {
  adHocItems: PropTypes.arrayOf(PropTypes.object).isRequired,
  hasListItems: PropTypes.bool.isRequired,
  onLaunchLoading: PropTypes.func.isRequired,
  moduleOptions: PropTypes.arrayOf(PropTypes.array).isRequired,
};

export default AdHocCommands;
