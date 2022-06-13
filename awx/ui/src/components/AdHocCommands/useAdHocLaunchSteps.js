import { useEffect, useState } from 'react';
import { useFormikContext } from 'formik';
import useCredentialPasswordsStep from './useAdHocCredentialPasswordStep';
import useAdHocDetailsStep from './useAdHocDetailsStep';
import useAdHocExecutionEnvironmentStep from './useAdHocExecutionEnvironmentStep';
import useAdHocCredentialStep from './useAdHocCredentialStep';
import useAdHocPreviewStep from './useAdHocPreviewStep';

function showCredentialPasswordsStep(credential) {
  if (!credential?.inputs) {
    return false;
  }
  const { inputs } = credential;
  if (
    inputs?.password === 'ASK' ||
    inputs?.become_password === 'ASK' ||
    inputs?.ssh_key_unlock === 'ASK'
  ) {
    return true;
  }

  return false;
}

export default function useAdHocLaunchSteps(
  moduleOptions,
  verbosityOptions,
  organizationId,
  credentialTypeId
) {
  const { values, resetForm, touched } = useFormikContext();

  const [visited, setVisited] = useState({});
  const steps = [
    useAdHocDetailsStep(visited, moduleOptions, verbosityOptions),
    useAdHocExecutionEnvironmentStep(organizationId),
    useAdHocCredentialStep(visited, credentialTypeId),
    useCredentialPasswordsStep(
      showCredentialPasswordsStep(values.credentials[0]),
      visited
    ),
  ];

  useEffect(() => {
    const newFormValues = { ...values };

    if (!values.credentials[0]?.inputs) {
      return;
    }
    if (
      (values.credentials[0].inputs?.password ||
        values.credentials[0].inputs?.become_password ||
        values.credentials[0].inputs?.ssh_key_unlock) === 'ASK'
    )
      newFormValues.credential_passwords = {};
    Object.keys(values.credentials[0].inputs).forEach((inputKey) => {
      if (inputKey === 'become_password' || inputKey === 'ssh_key_unlock') {
        newFormValues.credential_passwords[inputKey] = '';
      }
      if (inputKey === 'password') {
        newFormValues.credential_passwords.ssh_password = '';
      }
    });
    resetForm({
      values: newFormValues,
      touched,
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [values.credentials.length]);

  const hasErrors = steps.some((step) => step.hasError);

  steps.push(useAdHocPreviewStep(hasErrors));
  return {
    steps: steps.map((s) => s.step).filter((s) => s != null),
    validateStep: (stepId) =>
      steps.find((s) => s?.step.id === stepId).validate(),
    visitStep: (prevStepId, setFieldTouched) => {
      setVisited({
        ...visited,
        [prevStepId]: true,
      });
      steps.find((s) => s?.step?.id === prevStepId).setTouched(setFieldTouched);
    },
    visitAllSteps: (setFieldTouched) => {
      setVisited({
        details: true,
        executionEnvironment: true,
        credentials: true,
        credentialPasswords: true,
        preview: true,
      });
      steps.forEach((s) => s.setTouched(setFieldTouched));
    },
  };
}
