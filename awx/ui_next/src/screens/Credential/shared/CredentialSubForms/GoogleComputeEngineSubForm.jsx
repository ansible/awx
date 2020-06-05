import React, { useState } from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import {
  FileUpload,
  FormGroup,
  TextArea,
  TextInput,
} from '@patternfly/react-core';
import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../../components/FormLayout';
import { required } from '../../../../util/validators';
import { CredentialPluginField } from '../CredentialPlugins';

const GoogleComputeEngineSubForm = ({ i18n }) => {
  const [fileError, setFileError] = useState(null);
  const [filename, setFilename] = useState('');
  const [file, setFile] = useState('');
  const inputsUsernameHelpers = useField({
    name: 'inputs.username',
  })[2];
  const inputsProjectHelpers = useField({
    name: 'inputs.project',
  })[2];
  const inputsSSHKeyDataHelpers = useField({
    name: 'inputs.ssh_key_data',
  })[2];

  return (
    <FormColumnLayout>
      <FormGroup
        fieldId="credential-gce-file"
        isValid={!fileError}
        label={i18n._(t`Service account JSON file`)}
        helperText={i18n._(
          t`Select a JSON formatted service account key to autopopulate the following fields.`
        )}
        helperTextInvalid={fileError}
      >
        <FileUpload
          id="credential-gce-file"
          value={file}
          filename={filename}
          filenamePlaceholder={i18n._(t`Choose a .json file`)}
          onChange={async value => {
            if (value) {
              try {
                setFile(value);
                setFilename(value.name);
                const fileText = await value.text();
                const fileJSON = JSON.parse(fileText);
                if (
                  !fileJSON.client_email &&
                  !fileJSON.project_id &&
                  !fileJSON.private_key
                ) {
                  setFileError(
                    i18n._(
                      t`Expected at least one of client_email, project_id or private_key to be present in the file.`
                    )
                  );
                } else {
                  inputsUsernameHelpers.setValue(fileJSON.client_email || '');
                  inputsProjectHelpers.setValue(fileJSON.project_id || '');
                  inputsSSHKeyDataHelpers.setValue(fileJSON.private_key || '');
                  setFileError(null);
                }
              } catch {
                setFileError(
                  i18n._(
                    t`There was an error parsing the file. Please check the file formatting and try again.`
                  )
                );
              }
            } else {
              setFile('');
              setFilename('');
              inputsUsernameHelpers.setValue('');
              inputsProjectHelpers.setValue('');
              inputsSSHKeyDataHelpers.setValue('');
              setFileError(null);
            }
          }}
          dropzoneProps={{
            accept: '.json',
            onDropRejected: () => {
              setFileError(
                i18n._(
                  t`File upload rejected. Please select a single .json file.`
                )
              );
            },
          }}
        />
      </FormGroup>
      <CredentialPluginField
        id="credential-username"
        label={i18n._(t`Service account email address`)}
        name="inputs.username"
        type="email"
        validate={required(null, i18n)}
        isRequired
      >
        <TextInput id="credential-username" />
      </CredentialPluginField>
      <CredentialPluginField
        id="credential-project"
        label={i18n._(t`Project`)}
        name="inputs.project"
      >
        <TextInput id="credential-project" />
      </CredentialPluginField>
      <FormFullWidthLayout>
        <CredentialPluginField
          id="credential-sshKeyData"
          label={i18n._(t`RSA private key`)}
          name="inputs.ssh_key_data"
          type="textarea"
          validate={required(null, i18n)}
          isRequired
        >
          <TextArea
            id="credential-sshKeyData"
            rows={6}
            resizeOrientation="vertical"
          />
        </CredentialPluginField>
      </FormFullWidthLayout>
    </FormColumnLayout>
  );
};

export default withI18n()(GoogleComputeEngineSubForm);
