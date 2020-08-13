import React, { useState, Fragment, useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import useRequest, { useDismissableError } from '../../util/useRequest';
import AlertModal from '../AlertModal';
import { CredentialTypesAPI } from '../../api';
import ErrorDetail from '../ErrorDetail';
import AdHocCommandsWizard from './AdHocCommandsWizard';
import ContentLoading from '../ContentLoading';
import ContentError from '../ContentError';

function AdHocCommands({ children, apiModule, adHocItems, itemId, i18n }) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const history = useHistory();
  const verbosityOptions = [
    { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
    { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
    { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
    { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
    { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
  ];
  const {
    error: fetchError,
    request: fetchModuleOptions,
    result: { moduleOptions, credentialTypeId },
  } = useRequest(
    useCallback(async () => {
      const [choices, credId] = await Promise.all([
        apiModule.readAdHocOptions(itemId),
        CredentialTypesAPI.read({ namespace: 'ssh' }),
      ]);
      const itemObject = (item, index) => {
        return {
          key: index,
          value: item,
          label: `${item}`,
          isDisabled: false,
        };
      };

      const options = choices.data.actions.GET.module_name.choices.map(
        (choice, index) => itemObject(choice[0], index)
      );

      return {
        moduleOptions: [itemObject('', -1), ...options],
        credentialTypeId: credId.data.results[0].id,
      };
    }, [itemId, apiModule]),
    { moduleOptions: [] }
  );

  useEffect(() => {
    fetchModuleOptions();
  }, [fetchModuleOptions]);

  const {
    isloading: isLaunchLoading,
    error: launchError,
    request: launchAdHocCommands,
  } = useRequest(
    useCallback(
      async values => {
        const { data } = await apiModule.launchAdHocCommands(itemId, values);
        history.push(`/jobs/${data.module_name}/${data.id}/output`);
      },

      [apiModule, itemId, history]
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
    setIsWizardOpen(false);
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
    <Fragment>
      {children({
        openAdHocCommands: () => setIsWizardOpen(true),
      })}

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
    </Fragment>
  );
}

AdHocCommands.propTypes = {
  children: PropTypes.func.isRequired,
  adHocItems: PropTypes.arrayOf(PropTypes.object).isRequired,
  itemId: PropTypes.number.isRequired,
};

export default withI18n()(AdHocCommands);
