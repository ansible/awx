import { useState, useEffect } from 'react';
import { useFormikContext } from 'formik';
import useInventoryStep from './steps/useInventoryStep';
import useCredentialsStep from './steps/useCredentialsStep';
import useCredentialPasswordsStep from './steps/useCredentialPasswordsStep';
import useExecutionEnvironmentStep from './steps/useExecutionEnvironmentStep';
import useOtherPromptsStep from './steps/useOtherPromptsStep';
import useSurveyStep from './steps/useSurveyStep';
import usePreviewStep from './steps/usePreviewStep';
import useInstanceGroupsStep from './steps/useInstanceGroupsStep';

function showCredentialPasswordsStep(launchConfig, credentials = []) {
  if (
    !launchConfig?.ask_credential_on_launch &&
    launchConfig?.passwords_needed_to_start
  ) {
    return launchConfig.passwords_needed_to_start.length > 0;
  }

  let credentialPasswordStepRequired = false;

  credentials.forEach((credential) => {
    if (!credential.inputs) {
      const launchConfigCredential = launchConfig.defaults.credentials.find(
        (defaultCred) => defaultCred.id === credential.id
      );

      if (launchConfigCredential?.passwords_needed.length > 0) {
        credentialPasswordStepRequired = true;
      }
    } else if (
      credential?.inputs?.password === 'ASK' ||
      credential?.inputs?.become_password === 'ASK' ||
      credential?.inputs?.ssh_key_unlock === 'ASK' ||
      credential?.inputs?.vault_password === 'ASK'
    ) {
      credentialPasswordStepRequired = true;
    }
  });

  return credentialPasswordStepRequired;
}

export default function useLaunchSteps(
  launchConfig,
  surveyConfig,
  resource,
  labels,
  instanceGroups,
  resourceDefaultCredentials
) {
  const [visited, setVisited] = useState({});
  const [isReady, setIsReady] = useState(false);
  const { touched, values: formikValues } = useFormikContext();
  const steps = [
    useInventoryStep(launchConfig, resource, visited),
    useCredentialsStep(
      launchConfig,
      resource,
      resourceDefaultCredentials,
      true
    ),
    useCredentialPasswordsStep(
      launchConfig,
      showCredentialPasswordsStep(launchConfig, formikValues.credentials),
      visited
    ),
    useExecutionEnvironmentStep(launchConfig, resource),
    useInstanceGroupsStep(launchConfig, resource, instanceGroups),
    useOtherPromptsStep(launchConfig, resource, labels),
    useSurveyStep(launchConfig, surveyConfig, resource, visited),
  ];
  const { resetForm } = useFormikContext();
  const hasErrors = steps.some((step) => step.hasError);

  steps.push(
    usePreviewStep(launchConfig, resource, surveyConfig, hasErrors, true)
  );

  const pfSteps = steps.map((s) => s.step).filter((s) => s != null);
  const stepsAreReady = !steps.some((s) => !s.isReady);

  useEffect(() => {
    if (!stepsAreReady) {
      return;
    }

    const initialValues = steps.reduce(
      (acc, cur) => ({
        ...acc,
        ...cur.initialValues,
      }),
      {}
    );

    const newFormValues = { ...initialValues };

    Object.keys(formikValues).forEach((formikValueKey) => {
      if (
        formikValueKey === 'credential_passwords' &&
        Object.prototype.hasOwnProperty.call(
          newFormValues,
          'credential_passwords'
        )
      ) {
        const formikCredentialPasswords = formikValues.credential_passwords;
        Object.keys(formikCredentialPasswords).forEach(
          (credentialPasswordValueKey) => {
            if (
              Object.prototype.hasOwnProperty.call(
                newFormValues.credential_passwords,
                credentialPasswordValueKey
              )
            ) {
              newFormValues.credential_passwords[credentialPasswordValueKey] =
                formikCredentialPasswords[credentialPasswordValueKey];
            }
          }
        );
      } else if (
        Object.prototype.hasOwnProperty.call(newFormValues, formikValueKey)
      ) {
        newFormValues[formikValueKey] = formikValues[formikValueKey];
      }
    });

    resetForm({
      values: newFormValues,
      touched,
    });

    setIsReady(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [formikValues.credentials, stepsAreReady]);

  const stepWithError = steps.find((s) => s.contentError);
  const contentError = stepWithError ? stepWithError.contentError : null;

  return {
    steps: pfSteps,
    isReady,
    validateStep: (stepId) => {
      steps.find((s) => s?.step?.id === stepId).validate();
    },
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find((s) => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: (setFieldTouched) => {
      setVisited({
        inventory: true,
        credentials: true,
        credentialPasswords: true,
        executionEnvironment: true,
        instanceGroups: true,
        other: true,
        survey: true,
        preview: true,
      });
      steps.forEach((s) => s.setTouched(setFieldTouched));
    },
    contentError,
  };
}
