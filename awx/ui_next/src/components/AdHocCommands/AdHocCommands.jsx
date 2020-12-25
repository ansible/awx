import React, { useCallback, useEffect, useState, useContext } from 'react';
import { useHistory, useParams } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';
import { Button, DropdownItem } from '@patternfly/react-core';

import useRequest, { useDismissableError } from '../../util/useRequest';
import { InventoriesAPI, CredentialTypesAPI } from '../../api';

import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import AdHocCommandsWizard from './AdHocCommandsWizard';
import { KebabifiedContext } from '../../contexts/Kebabified';
import ContentLoading from '../ContentLoading';
import ContentError from '../ContentError';

function AdHocCommands({ adHocItems, i18n, hasListItems }) {
  const history = useHistory();
  const { id } = useParams();

  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const { isKebabified, onKebabModalChange } = useContext(KebabifiedContext);

  const verbosityOptions = [
    { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
    { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
    { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
    { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
    { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
  ];
  useEffect(() => {
    if (isKebabified) {
      onKebabModalChange(isWizardOpen);
    }
  }, [isKebabified, isWizardOpen, onKebabModalChange]);

  const {
    result: { moduleOptions, credentialTypeId, isAdHocDisabled },
    request: fetchData,
    error: fetchError,
  } = useRequest(
    useCallback(async () => {
      const [options, cred] = await Promise.all([
        InventoriesAPI.readAdHocOptions(id),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
      ]);
      return {
        moduleOptions: options.data.actions.GET.module_name.choices,
        credentialTypeId: cred.data.results[0].id,
        isAdHocDisabled: !options.data.actions.POST,
      };
    }, [id]),
    { moduleOptions: [], isAdHocDisabled: true }
  );
  useEffect(() => {
    fetchData();
  }, [fetchData]);
  const {
    isloading: isLaunchLoading,
    error: launchError,
    request: launchAdHocCommands,
  } = useRequest(
    useCallback(
      async values => {
        const { data } = await InventoriesAPI.launchAdHocCommands(id, values);
        history.push(`/jobs/command/${data.id}/output`);
      },

      [id, history]
    )
  );

  const { error, dismissError } = useDismissableError(
    launchError || fetchError
  );

  const handleSubmit = async values => {
    const { credential, ...remainingValues } = values;
    const newCredential = credential[0].id;

    const manipulatedValues = {
      credential: newCredential,
      ...remainingValues,
    };
    await launchAdHocCommands(manipulatedValues);
  };

  if (isLaunchLoading) {
    return <ContentLoading />;
  }

  if (error && isWizardOpen) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => {
          dismissError();
          setIsWizardOpen(false);
        }}
      >
        {launchError ? (
          <>
            {i18n._(t`Failed to launch job.`)}
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
      {isKebabified ? (
        <DropdownItem
          key="cancel-job"
          isDisabled={isAdHocDisabled || !hasListItems}
          component="button"
          aria-label={i18n._(t`Run Command`)}
          onClick={() => setIsWizardOpen(true)}
        >
          {i18n._(t`Run Command`)}
        </DropdownItem>
      ) : (
        <Button
          variant="secondary"
          aria-label={i18n._(t`Run Command`)}
          onClick={() => setIsWizardOpen(true)}
          isDisabled={isAdHocDisabled || !hasListItems}
        >
          {i18n._(t`Run Command`)}
        </Button>
      )}

      {isWizardOpen && (
        <AdHocCommandsWizard
          adHocItems={adHocItems}
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

export default withI18n()(AdHocCommands);
