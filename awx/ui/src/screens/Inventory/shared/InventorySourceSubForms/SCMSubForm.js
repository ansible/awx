import React, { useCallback, useEffect, useState } from 'react';
import { useField, useFormikContext } from 'formik';
import { t } from '@lingui/macro';
import {
  FormGroup,
  SelectVariant,
  Select,
  SelectOption,
} from '@patternfly/react-core';
import { ProjectsAPI } from 'api';
import useRequest from 'hooks/useRequest';
import { required } from 'util/validators';
import CredentialLookup from 'components/Lookup/CredentialLookup';
import ProjectLookup from 'components/Lookup/ProjectLookup';
import Popover from 'components/Popover';
import {
  OptionsField,
  SourceVarsField,
  VerbosityField,
  EnabledVarField,
  EnabledValueField,
  HostFilterField,
} from './SharedFields';
import getHelpText from '../Inventory.helptext';

const SCMSubForm = ({ autoPopulateProject }) => {
  const helpText = getHelpText();
  const [isOpen, setIsOpen] = useState(false);
  const [sourcePath, setSourcePath] = useState([]);
  const { setFieldValue, setFieldTouched } = useFormikContext();
  const [credentialField] = useField('credential');

  const [projectField, projectMeta, projectHelpers] =
    useField('source_project');
  const [sourcePathField, sourcePathMeta, sourcePathHelpers] = useField({
    name: 'source_path',
    validate: required(t`Select a value for this field`),
  });

  const { error: sourcePathError, request: fetchSourcePath } = useRequest(
    useCallback(async (projectId) => {
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
    (value) => {
      setFieldValue('source_project', value);
      setFieldTouched('source_project', true, false);
      if (sourcePathField.value) {
        setFieldValue('source_path', '');
        setFieldTouched('source_path', false);
      }
      if (value) {
        fetchSourcePath(value.id);
      }
    },
    [fetchSourcePath, setFieldValue, setFieldTouched, sourcePathField.value]
  );

  const handleCredentialUpdate = useCallback(
    (value) => {
      setFieldValue('credential', value);
      setFieldTouched('credential', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <CredentialLookup
        credentialTypeKind="cloud"
        label={t`Credential`}
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
        fieldName="source_project"
        validate={required(t`Select a value for this field`)}
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
        label={t`Inventory file`}
        labelIcon={<Popover content={helpText.sourcePath} />}
      >
        <Select
          ouiaId="InventorySourceForm-source_path"
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
            sourcePathHelpers.setValue(value);
          }}
          aria-label={t`Select source path`}
          typeAheadAriaLabel={t`Select source path`}
          placeholder={t`Select source path`}
          createText={t`Set source path to`}
          isCreatable
          onCreateOption={(value) => {
            value.trim();
            setSourcePath([...sourcePath, value]);
          }}
          noResultsFoundText={t`No results found`}
        >
          {sourcePath.map((path) => (
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

export default SCMSubForm;
