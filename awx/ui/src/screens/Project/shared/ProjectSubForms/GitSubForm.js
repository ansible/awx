import 'styled-components/macro';
import React, { useCallback } from 'react';
import { t } from '@lingui/macro';
import { useFormikContext } from 'formik';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import FormField from 'components/FormField';
import getDocsBaseUrl from 'util/getDocsBaseUrl';
import { useConfig } from 'contexts/Config';

import {
  UrlFormField,
  BranchFormField,
  ScmCredentialFormField,
  ScmTypeOptions,
} from './SharedFields';

import projectHelpStrings from '../Project.helptext';

const GitSubForm = ({
  credential,
  signature_validation_credential,
  onCredentialSelection,
  onSignatureValidationCredentialSelection,
  scmUpdateOnLaunch,
}) => {
  const { setFieldValue, setFieldTouched } = useFormikContext();

  const onCredentialChange = useCallback(
    (value) => {
      onSignatureValidationCredentialSelection('cryptography', value);
      setFieldValue('signature_validation_credential', value);
      setFieldTouched('signature_validation_credential', true, false);
    },
    [onSignatureValidationCredentialSelection, setFieldValue, setFieldTouched]
  );

  const docsURL = `${getDocsBaseUrl(
    useConfig()
  )}/html/userguide/projects.html#manage-playbooks-using-source-control`;

  return (
    <>
      <UrlFormField tooltip={projectHelpStrings.githubSourceControlUrl} />
      <BranchFormField label={t`Source Control Branch/Tag/Commit`} />
      <FormField
        id="project-scm-refspec"
        label={t`Source Control Refspec`}
        name="scm_refspec"
        type="text"
        tooltipMaxWidth="400px"
        tooltip={projectHelpStrings.sourceControlRefspec(docsURL)}
      />
      <CredentialLookup
        credentialTypeId={signature_validation_credential.typeId}
        label={t`Content Signature Validation Credential`}
        onChange={onCredentialChange}
        value={signature_validation_credential.value}
        tooltip={projectHelpStrings.signatureValidation}
      />
      <ScmCredentialFormField
        credential={credential}
        onCredentialSelection={onCredentialSelection}
      />
      <ScmTypeOptions scmUpdateOnLaunch={scmUpdateOnLaunch} />
    </>
  );
};

export default GitSubForm;
