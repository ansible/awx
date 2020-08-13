import React, { useState, Fragment, useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import useRequest, { useDismissableError } from '../../util/useRequest';
import AlertModal from '../AlertModal';
import { CredentialTypesAPI } from '../../api';
import ErrorDetail from '../ErrorDetail';
import AdHocCommandsForm from './AdHocCommandsWizard';
import ContentLoading from '../ContentLoading';
import ContentError from '../ContentError';

function AdHocCommands({ children, apiModule, adHocItems, itemId, i18n }) {
  const [isWizardOpen, setIsWizardOpen] = useState(false);
  const history = useHistory();

  const {
    error: fetchError,
    request: fetchModuleOptions,
    result: { moduleOptions, verbosityOptions, credentialTypeId },
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

      const verbosityItems = choices.data.actions.GET.verbosity.choices.map(
        (choice, index) => itemObject(choice[0], index)
      );

      return {
        moduleOptions: [itemObject('', -1), ...options],
        verbosityOptions: [itemObject('', -1), ...verbosityItems],
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

  const handleSubmit = async (values, limitTypedValue) => {
    const { credential, limit, ...remainingValues } = values;
    const newCredential = credential[0].id;
    if (limitTypedValue) {
      values.limit = limit.concat(limitTypedValue);
    }
    const stringifyLimit = values.limit.join(', ').trim();

    const manipulatedValues = {
      limit: stringifyLimit[0],
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
        <ContentError error={error} />
      </AlertModal>
    );
  }
  return (
    <Fragment>
      {children({
        openAdHocCommands: () => setIsWizardOpen(true),
      })}

      {isWizardOpen && (
        <AdHocCommandsForm
          adHocItems={adHocItems}
          moduleOptions={moduleOptions}
          verbosityOptions={verbosityOptions}
          credentialTypeId={credentialTypeId}
          onCloseWizard={() => setIsWizardOpen(false)}
          onLaunch={handleSubmit}
          error={error}
          onDismissError={() => dismissError()}
        />
      )}
      {launchError && (
        <AlertModal
          isOpen={error}
          variant="error"
          title={i18n._(t`Error!`)}
          onClose={dismissError}
        >
          {i18n._(t`Failed to launch job.`)}
          <ErrorDetail error={error} />
        </AlertModal>
      )}
    </Fragment>
  );
}

export default withI18n()(AdHocCommands);
