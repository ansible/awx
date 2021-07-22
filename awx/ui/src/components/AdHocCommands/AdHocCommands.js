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

  const verbosityOptions = [
    { value: '0', key: '0', label: t`0 (Normal)` },
    { value: '1', key: '1', label: t`1 (Verbose)` },
    { value: '2', key: '2', label: t`2 (More Verbose)` },
    { value: '3', key: '3', label: t`3 (Debug)` },
    { value: '4', key: '4', label: t`4 (Connection Debug)` },
  ];
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
    const { credential, execution_environment, ...remainingValues } = values;
    const newCredential = credential[0].id;

    const manipulatedValues = {
      credential: newCredential,
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
          verbosityOptions={verbosityOptions}
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
};

export default AdHocCommands;
