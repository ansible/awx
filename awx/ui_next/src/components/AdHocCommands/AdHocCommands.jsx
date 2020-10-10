import React, { useCallback } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import PropTypes from 'prop-types';

import useRequest, { useDismissableError } from '../../util/useRequest';
import { InventoriesAPI } from '../../api';

import AlertModal from '../AlertModal';
import ErrorDetail from '../ErrorDetail';
import AdHocCommandsWizard from './AdHocCommandsWizard';
import ContentLoading from '../ContentLoading';

function AdHocCommands({
  onClose,
  adHocItems,
  itemId,
  i18n,
  moduleOptions,
  credentialTypeId,
}) {
  const history = useHistory();
  const verbosityOptions = [
    { value: '0', key: '0', label: i18n._(t`0 (Normal)`) },
    { value: '1', key: '1', label: i18n._(t`1 (Verbose)`) },
    { value: '2', key: '2', label: i18n._(t`2 (More Verbose)`) },
    { value: '3', key: '3', label: i18n._(t`3 (Debug)`) },
    { value: '4', key: '4', label: i18n._(t`4 (Connection Debug)`) },
  ];

  const {
    isloading: isLaunchLoading,
    error,
    request: launchAdHocCommands,
  } = useRequest(
    useCallback(
      async values => {
        const { data } = await InventoriesAPI.launchAdHocCommands(
          itemId,
          values
        );
        history.push(`/jobs/command/${data.id}/output`);
      },

      [itemId, history]
    )
  );

  const { dismissError } = useDismissableError(error);

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

  if (error) {
    return (
      <AlertModal
        isOpen={error}
        variant="error"
        title={i18n._(t`Error!`)}
        onClose={() => {
          dismissError();
        }}
      >
        <>
          {i18n._(t`Failed to launch job.`)}
          <ErrorDetail error={error} />
        </>
      </AlertModal>
    );
  }
  return (
    <AdHocCommandsWizard
      adHocItems={adHocItems}
      moduleOptions={moduleOptions}
      verbosityOptions={verbosityOptions}
      credentialTypeId={credentialTypeId}
      onCloseWizard={onClose}
      onLaunch={handleSubmit}
      onDismissError={() => dismissError()}
    />
  );
}

AdHocCommands.propTypes = {
  adHocItems: PropTypes.arrayOf(PropTypes.object).isRequired,
  itemId: PropTypes.number.isRequired,
};

export default withI18n()(AdHocCommands);
