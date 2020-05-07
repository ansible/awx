import React, { useCallback } from 'react';
import { useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { ProjectsAPI } from '@api';
import useRequest from '@util/useRequest';
import { required } from '@util/validators';

import { FormGroup } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import { FieldTooltip } from '@components/FormField';
import CredentialLookup from '@components/Lookup/CredentialLookup';
import ProjectLookup from '@components/Lookup/ProjectLookup';
import { VerbosityField, OptionsField, SourceVarsField } from './SharedFields';

const SCMSubForm = ({ i18n }) => {
  const [credentialField, , credentialHelpers] = useField('credential');
  const [projectField, projectMeta, projectHelpers] = useField({
    name: 'source_project',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [sourcePathField, sourcePathMeta, sourcePathHelpers] = useField({
    name: 'source_path',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const {
    error: sourcePathError,
    request: fetchSourcePath,
    result: sourcePath,
  } = useRequest(
    useCallback(async projectId => {
      const { data } = await ProjectsAPI.readInventories(projectId);
      return [...data, '/ (project root)'];
    }, []),
    []
  );

  const handleProjectUpdate = useCallback(
    value => {
      projectHelpers.setValue(value);
      fetchSourcePath(value.id);
      sourcePathHelpers.setValue('');
    },
    [] // eslint-disable-line react-hooks/exhaustive-deps
  );

  return (
    <>
      <CredentialLookup
        credentialTypeKind="cloud"
        label={i18n._(t`Credential`)}
        value={credentialField.value}
        onChange={value => {
          credentialHelpers.setValue(value);
        }}
      />
      <ProjectLookup
        value={projectField.value}
        isValid={!projectMeta.touched || !projectMeta.error}
        helperTextInvalid={projectMeta.error}
        onBlur={() => projectHelpers.setTouched()}
        onChange={handleProjectUpdate}
        required
      />
      <FormGroup
        fieldId="source_path"
        helperTextInvalid={sourcePathError?.message || sourcePathMeta.error}
        isValid={
          !sourcePathError?.message ||
          !sourcePathMeta.error ||
          !sourcePathMeta.touched
        }
        isRequired
        label={i18n._(t`Inventory file`)}
      >
        <FieldTooltip
          content={i18n._(t`Select the inventory file
          to be synced by this source. You can select from
          the dropdown or enter a file within the input.`)}
        />
        <AnsibleSelect
          {...sourcePathField}
          id="source_path"
          isValid={!sourcePathMeta.touched || !sourcePathMeta.error}
          data={[
            {
              value: '',
              key: '',
              label: i18n._(t`Choose an inventory file`),
              isDisabled: true,
            },
            ...sourcePath.map(value => ({ value, label: value, key: value })),
          ]}
          onChange={(event, value) => {
            sourcePathHelpers.setValue(value);
          }}
        />
      </FormGroup>
      <VerbosityField />
      <OptionsField />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(SCMSubForm);
