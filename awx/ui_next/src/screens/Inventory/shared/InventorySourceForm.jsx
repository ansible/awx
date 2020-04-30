import React, { useEffect, useCallback, useContext } from 'react';
import { Formik, useField } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { InventorySourcesAPI } from '@api';
import { ConfigContext } from '@contexts/Config';
import useRequest from '@util/useRequest';
import { required } from '@util/validators';

import { Form, FormGroup, Title } from '@patternfly/react-core';
import AnsibleSelect from '@components/AnsibleSelect';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import FormField, {
  FieldTooltip,
  FormSubmitError,
} from '@components/FormField';
import { FormColumnLayout, SubFormLayout } from '@components/FormLayout';

import SCMSubForm from './InventorySourceSubForms';

const InventorySourceFormFields = ({ sourceOptions, i18n }) => {
  const [sourceField, sourceMeta, sourceHelpers] = useField({
    name: 'source',
    validate: required(i18n._(t`Set a value for this field`), i18n),
  });
  const { custom_virtualenvs } = useContext(ConfigContext);
  const [venvField] = useField('custom_virtualenv');
  const defaultVenv = {
    label: i18n._(t`Use Default Ansible Environment`),
    value: '/venv/ansible/',
    key: 'default',
  };

  return (
    <>
      <FormField
        id="name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <FormGroup
        fieldId="source"
        helperTextInvalid={sourceMeta.error}
        isRequired
        isValid={!sourceMeta.touched || !sourceMeta.error}
        label={i18n._(t`Source`)}
      >
        <AnsibleSelect
          {...sourceField}
          id="source"
          data={[
            {
              value: '',
              key: '',
              label: i18n._(t`Choose a source`),
              isDisabled: true,
            },
            ...sourceOptions,
          ]}
          onChange={(event, value) => {
            sourceHelpers.setValue(value);
          }}
        />
      </FormGroup>
      {custom_virtualenvs && custom_virtualenvs.length > 1 && (
        <FormGroup
          fieldId="custom-virtualenv"
          label={i18n._(t`Ansible Environment`)}
        >
          <FieldTooltip
            content={i18n._(t`Select the custom
            Python virtual environment for this
            inventory source sync to run on.`)}
          />
          <AnsibleSelect
            id="custom-virtualenv"
            data={[
              defaultVenv,
              ...custom_virtualenvs
                .filter(value => value !== defaultVenv.value)
                .map(value => ({ value, label: value, key: value })),
            ]}
            {...venvField}
          />
        </FormGroup>
      )}

      {sourceField.value !== '' && (
        <SubFormLayout>
          <Title size="md">{i18n._(t`Source details`)}</Title>
          <FormColumnLayout>
            {
              {
                scm: <SCMSubForm />,
              }[sourceField.value]
            }
          </FormColumnLayout>
        </SubFormLayout>
      )}
    </>
  );
};

const InventorySourceForm = ({
  i18n,
  onCancel,
  onSubmit,
  submitError = null,
}) => {
  const initialValues = {
    credential: null,
    custom_virtualenv: '',
    description: '',
    name: '',
    overwrite: false,
    overwrite_vars: false,
    source: '',
    source_path: '',
    source_project: null,
    source_vars: '---\n',
    update_cache_timeout: 0,
    update_on_launch: false,
    update_on_project_update: false,
    verbosity: 1,
  };

  const {
    isLoading: isSourceOptionsLoading,
    error: sourceOptionsError,
    request: fetchSourceOptions,
    result: sourceOptions,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventorySourcesAPI.readOptions();
      const sourceChoices = Object.assign(
        ...data.actions.GET.source.choices.map(([key, val]) => ({ [key]: val }))
      );
      delete sourceChoices.file;
      return Object.keys(sourceChoices).map(choice => {
        return {
          value: choice,
          key: choice,
          label: sourceChoices[choice],
        };
      });
    }, []),
    []
  );

  useEffect(() => {
    fetchSourceOptions();
  }, [fetchSourceOptions]);

  if (isSourceOptionsLoading) {
    return <ContentLoading />;
  }

  if (sourceOptionsError) {
    return <ContentError error={sourceOptionsError} />;
  }

  return (
    <Formik
      initialValues={initialValues}
      onSubmit={values => {
        onSubmit(values);
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <InventorySourceFormFields
              formik={formik}
              i18n={i18n}
              sourceOptions={sourceOptions}
            />
            {submitError && <FormSubmitError error={submitError} />}
            <FormActionGroup
              onCancel={onCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
};

export default withI18n()(InventorySourceForm);
