import React, { useEffect, useCallback, useContext } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { func, shape } from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import { InventorySourcesAPI } from '../../../api';
import { ConfigContext } from '../../../contexts/Config';
import useRequest from '../../../util/useRequest';
import { required } from '../../../util/validators';

import AnsibleSelect from '../../../components/AnsibleSelect';
import ContentError from '../../../components/ContentError';
import ContentLoading from '../../../components/ContentLoading';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import {
  FormColumnLayout,
  SubFormLayout,
} from '../../../components/FormLayout';
import Popover from '../../../components/Popover';

import {
  AzureSubForm,
  EC2SubForm,
  GCESubForm,
  OpenStackSubForm,
  SCMSubForm,
  SatelliteSubForm,
  TowerSubForm,
  VMwareSubForm,
  VirtualizationSubForm,
} from './InventorySourceSubForms';

const buildSourceChoiceOptions = options => {
  const sourceChoices = options.actions.GET.source.choices.map(
    ([choice, label]) => ({ label, key: choice, value: choice })
  );
  return sourceChoices.filter(({ key }) => key !== 'file');
};

const InventorySourceFormFields = ({ source, sourceOptions, i18n }) => {
  const {
    values,
    initialValues,
    resetForm,
    setFieldTouched,
    setFieldValue,
  } = useFormikContext();
  const [sourceField, sourceMeta] = useField({
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

  const resetSubFormFields = sourceType => {
    if (sourceType === initialValues.source) {
      resetForm({
        values: {
          ...initialValues,
          name: values.name,
          description: values.description,
          custom_virtualenv: values.custom_virtualenv,
          source: sourceType,
        },
      });
    } else {
      const defaults = {
        credential: null,
        overwrite: false,
        overwrite_vars: false,
        source: sourceType,
        source_path: '',
        source_project: null,
        source_script: null,
        source_vars: '---\n',
        update_cache_timeout: 0,
        update_on_launch: false,
        update_on_project_update: false,
        verbosity: 1,
        enabled_var: '',
        enabled_value: '',
        host_filter: '',
      };
      Object.keys(defaults).forEach(label => {
        setFieldValue(label, defaults[label]);
        setFieldTouched(label, false);
      });
    }
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
        validated={
          !sourceMeta.touched || !sourceMeta.error ? 'default' : 'error'
        }
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
            ...buildSourceChoiceOptions(sourceOptions),
          ]}
          onChange={(event, value) => {
            resetSubFormFields(value);
          }}
        />
      </FormGroup>
      {custom_virtualenvs && custom_virtualenvs.length > 1 && (
        <FormGroup
          fieldId="custom-virtualenv"
          label={i18n._(t`Ansible Environment`)}
          labelIcon={
            <Popover
              content={i18n._(t`Select the custom
            Python virtual environment for this
            inventory source sync to run on.`)}
            />
          }
        >
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
          <Title size="md" headingLevel="h4">
            {i18n._(t`Source details`)}
          </Title>
          <FormColumnLayout>
            {
              {
                azure_rm: (
                  <AzureSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'azure_rm'
                    }
                    sourceOptions={sourceOptions}
                  />
                ),
                ec2: <EC2SubForm sourceOptions={sourceOptions} />,
                gce: (
                  <GCESubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'gce'
                    }
                    sourceOptions={sourceOptions}
                  />
                ),
                openstack: (
                  <OpenStackSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'openstack'
                    }
                  />
                ),
                rhv: (
                  <VirtualizationSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'rhv'
                    }
                  />
                ),
                satellite6: (
                  <SatelliteSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'satellite6'
                    }
                  />
                ),
                scm: (
                  <SCMSubForm
                    autoPopulateProject={
                      !source?.id || source?.source !== 'scm'
                    }
                  />
                ),
                tower: (
                  <TowerSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'tower'
                    }
                  />
                ),
                vmware: (
                  <VMwareSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'vmware'
                    }
                    sourceOptions={sourceOptions}
                  />
                ),
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
  source,
  submitError = null,
}) => {
  const initialValues = {
    credential: source?.summary_fields?.credential || null,
    custom_virtualenv: source?.custom_virtualenv || '',
    description: source?.description || '',
    name: source?.name || '',
    overwrite: source?.overwrite || false,
    overwrite_vars: source?.overwrite_vars || false,
    source: source?.source || '',
    source_path: source?.source_path || '',
    source_project: source?.summary_fields?.source_project || null,
    source_script: source?.summary_fields?.source_script || null,
    source_vars: source?.source_vars || '---\n',
    update_cache_timeout: source?.update_cache_timeout || 0,
    update_on_launch: source?.update_on_launch || false,
    update_on_project_update: source?.update_on_project_update || false,
    verbosity: source?.verbosity || 1,
    enabled_var: source?.enabled_var || '',
    enabled_value: source?.enabled_value || '',
    host_filter: source?.host_filter || '',
  };

  const {
    isLoading: isSourceOptionsLoading,
    error: sourceOptionsError,
    request: fetchSourceOptions,
    result: sourceOptions,
  } = useRequest(
    useCallback(async () => {
      const { data } = await InventorySourcesAPI.readOptions();
      return data;
    }, []),
    null
  );

  useEffect(() => {
    fetchSourceOptions();
  }, [fetchSourceOptions]);

  if (sourceOptionsError) {
    return <ContentError error={sourceOptionsError} />;
  }

  if (!sourceOptions || isSourceOptionsLoading) {
    return <ContentLoading />;
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
              source={source}
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

InventorySourceForm.propTypes = {
  onCancel: func.isRequired,
  onSubmit: func.isRequired,
  submitError: shape({}),
};

InventorySourceForm.defaultProps = {
  submitError: null,
};

export default withI18n()(InventorySourceForm);
