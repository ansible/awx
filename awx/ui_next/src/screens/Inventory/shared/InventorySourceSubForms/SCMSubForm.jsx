import React, { useCallback, useEffect, useState } from 'react';
import { useField, useFormikContext } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  FormGroup,
  SelectVariant,
  Select,
  SelectOption,
} from '@patternfly/react-core';
import { ProjectsAPI } from '../../../../api';
import useRequest from '../../../../util/useRequest';
import { required } from '../../../../util/validators';

import CredentialLookup from '../../../../components/Lookup/CredentialLookup';
import ProjectLookup from '../../../../components/Lookup/ProjectLookup';
import Popover from '../../../../components/Popover';
import {
  OptionsField,
  SourceVarsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
} from './SharedFields';

const SCMSubForm = ({ autoPopulateProject, i18n }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [sourcePath, setSourcePath] = useState([]);
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credentialField] = useField('credential');
  const [projectField, projectMeta, projectHelpers] = useField({
    name: 'source_project',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const [sourcePathField, sourcePathMeta, sourcePathHelpers] = useField({
    name: 'source_path',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  const { error: sourcePathError, request: fetchSourcePath } = useRequest(
    useCallback(async projectId => {
      const { data } = await ProjectsAPI.readInventories(projectId);
      setSourcePath([...data, '/ (project root)']);
    }, []),
    []
  );

  useEffect(() => {
    if (projectMeta.initialValue) {
      fetchSourcePath(projectMeta.initialValue.id);
      if (sourcePathField.value === '') {
        sourcePathHelpers.setValue('/ (project root)');
      }
    } // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchSourcePath, projectMeta.initialValue]);

  const handleProjectUpdate = useCallback(
    value => {
      setFieldValue('source_project', value);
      setFieldValue('source_path', '');
      setFieldTouched('source_path', false);
      fetchSourcePath(value.id);
    },
    [fetchSourcePath, setFieldValue, setFieldTouched]
  );

  const handleCredentialUpdate = useCallback(
    value => {
      setFieldValue('credential', value);
    },
    [setFieldValue]
  );

  return (
    <>
      <CredentialLookup
        credentialTypeKind="cloud"
        label={i18n._(t`Credential`)}
        value={credentialField.value}
        onChange={handleCredentialUpdate}
      />
      <ProjectLookup
        value={projectField.value}
        isValid={!projectMeta.touched || !projectMeta.error}
        helperTextInvalid={projectMeta.error}
        onBlur={() => projectHelpers.setTouched()}
        onChange={handleProjectUpdate}
        required
        autoPopulate={autoPopulateProject}
      />
      <FormGroup
        fieldId="source_path"
        helperTextInvalid={sourcePathError?.message || sourcePathMeta.error}
        validated={
          (!sourcePathMeta.error || !sourcePathMeta.touched) &&
          !sourcePathError?.message
            ? 'default'
            : 'error'
        }
        isRequired
        label={i18n._(t`Inventory file`)}
        labelIcon={
          <Popover
            content={i18n._(t`Select the inventory file
          to be synced by this source. You can select from
          the dropdown or enter a file within the input.`)}
          />
        }
      >
        <Select
          variant={SelectVariant.typeahead}
          onToggle={setIsOpen}
          isOpen={isOpen}
          selections={sourcePathField.value}
          id="source_path"
          isValid={
            (!sourcePathMeta.error || !sourcePathMeta.touched) &&
            !sourcePathError?.message
          }
          onSelect={(event, value) => {
            setIsOpen(false);
            value = value.trim();
            if (!value.endsWith('/')) {
              value += '/';
            }
            sourcePathHelpers.setValue(value);
          }}
          aria-label={i18n._(t`Select source path`)}
          placeholder={i18n._(t`Select source path`)}
          isCreatable
          onCreateOption={value => {
            value.trim();

            if (!value.endsWith('/')) {
              value += '/';
            }
            setSourcePath([...sourcePath, value]);
          }}
        >
          {sourcePath.map(path => (
            <SelectOption key={path} id={path} value={path} />
          ))}
        </Select>
      </FormGroup>
      <VerbosityField />
      <HostFilterField />
      <EnabledVarField />
      <EnabledValueField />
      <OptionsField showProjectUpdate />
      <SourceVarsField />
    </>
  );
};

export default withI18n()(SCMSubForm);
