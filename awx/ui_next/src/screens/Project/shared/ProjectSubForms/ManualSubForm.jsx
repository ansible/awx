import 'styled-components/macro';
import React from 'react';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { useField } from 'formik';
import { FormGroup, Alert } from '@patternfly/react-core';
import { required } from '../../../../util/validators';
import AnsibleSelect from '../../../../components/AnsibleSelect';
import FormField from '../../../../components/FormField';
import Popover from '../../../../components/Popover';
import { BrandName } from '../../../../variables';

// Setting BrandName to a variable here is necessary to get the jest tests
// passing.  Attempting to use BrandName in the template literal results
// in failing tests.
const brandName = BrandName;

const ManualSubForm = ({
  i18n,
  localPath,
  project_base_dir,
  project_local_paths,
}) => {
  const localPaths = [...new Set([...project_local_paths, localPath])];
  const options = [
    {
      value: '',
      key: '',
      label: i18n._(t`Choose a Playbook Directory`),
    },
    ...localPaths
      .filter(path => path)
      .map(path => ({
        value: path,
        key: path,
        label: path,
      })),
  ];
  const [pathField, pathMeta, pathHelpers] = useField({
    name: 'local_path',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });

  return (
    <>
      {options.length === 1 && (
        <Alert
          title={i18n._(t`WARNING: `)}
          css="grid-column: 1/-1"
          variant="warning"
          isInline
        >
          {i18n._(t`
            There are no available playbook directories in ${project_base_dir}.
            Either that directory is empty, or all of the contents are already
            assigned to other projects. Create a new directory there and make
            sure the playbook files can be read by the "awx" system user,
            or have ${brandName} directly retrieve your playbooks from
            source control using the Source Control Type option above.`)}
        </Alert>
      )}
      <FormField
        id="project-base-dir"
        label={i18n._(t`Project Base Path`)}
        name="base_dir"
        type="text"
        isReadOnly
        tooltip={
          <span>
            {i18n._(t`Base path used for locating playbooks. Directories
              found inside this path will be listed in the playbook directory drop-down.
              Together the base path and selected playbook directory provide the full
              path used to locate playbooks.`)}
            <br />
            <br />
            {i18n._(t`Change PROJECTS_ROOT when deploying
              ${brandName} to change this location.`)}
          </span>
        }
      />
      <FormGroup
        fieldId="project-local-path"
        helperTextInvalid={pathMeta.error}
        isRequired
        validated={!pathMeta.touched || !pathMeta.error ? 'default' : 'error'}
        label={i18n._(t`Playbook Directory`)}
        labelIcon={
          <Popover
            content={i18n._(t`Select from the list of directories found in
          the Project Base Path. Together the base path and the playbook
          directory provide the full path used to locate playbooks.`)}
          />
        }
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

export default withI18n()(ManualSubForm);
