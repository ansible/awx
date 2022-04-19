import 'styled-components/macro';
import React from 'react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup, Alert } from '@patternfly/react-core';
import { required } from 'util/validators';
import AnsibleSelect from 'components/AnsibleSelect';
import FormField from 'components/FormField';
import Popover from 'components/Popover';
import useBrandName from 'hooks/useBrandName';
import ProjectHelpStrings from '../Project.helptext';

const ManualSubForm = ({
  localPath,
  project_base_dir,
  project_local_paths,
}) => {
  const brandName = useBrandName();
  const projectHelpStrings = ProjectHelpStrings();

  const localPaths = [...new Set([...project_local_paths, localPath])];
  const options = [
    {
      value: '',
      key: '',
      label: t`Choose a Playbook Directory`,
    },
    ...localPaths
      .filter((path) => path)
      .map((path) => ({
        value: path,
        key: path,
        label: path,
      })),
  ];
  const [pathField, pathMeta, pathHelpers] = useField({
    name: 'local_path',
    validate: required(t`Select a value for this field`),
  });

  return (
    <>
      {options.length === 1 && (
        <Alert
          title={t`WARNING: `}
          css="grid-column: 1/-1"
          variant="warning"
          isInline
          ouiaId="project-manual-subform-alert"
        >
          {t`
            There are no available playbook directories in ${project_base_dir}.
            Either that directory is empty, or all of the contents are already
            assigned to other projects. Create a new directory there and make
            sure the playbook files can be read by the "awx" system user,
            or have ${brandName} directly retrieve your playbooks from
            source control using the Source Control Type option above.`}
        </Alert>
      )}
      <FormField
        id="project-base-dir"
        label={t`Project Base Path`}
        name="base_dir"
        type="text"
        isReadOnly
        tooltip={projectHelpStrings.projectBasePath}
      />
      <FormGroup
        fieldId="project-local-path"
        helperTextInvalid={pathMeta.error}
        isRequired
        validated={!pathMeta.touched || !pathMeta.error ? 'default' : 'error'}
        label={t`Playbook Directory`}
        labelIcon={<Popover content={projectHelpStrings.projectLocalPath} />}
      >
        <AnsibleSelect
          {...pathField}
          id="local_path"
          data={options}
          onChange={(event, value) => {
            pathHelpers.setValue(value);
          }}
        />
      </FormGroup>
    </>
  );
};

export default ManualSubForm;
