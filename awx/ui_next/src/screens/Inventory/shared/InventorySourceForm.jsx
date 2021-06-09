import React, { useEffect, useCallback } from 'react';
import { Formik, useField, useFormikContext } from 'formik';
import { func, shape } from 'prop-types';
import { t } from '@lingui/macro';
import { Form, FormGroup, Title } from '@patternfly/react-core';
import { InventorySourcesAPI } from '../../../api';
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

import {
  AzureSubForm,
  EC2SubForm,
  GCESubForm,
  InsightsSubForm,
  OpenStackSubForm,
  SCMSubForm,
  SatelliteSubForm,
  TowerSubForm,
  VMwareSubForm,
  VirtualizationSubForm,
} from './InventorySourceSubForms';
import { ExecutionEnvironmentLookup } from '../../../components/Lookup';

const buildSourceChoiceOptions = options => {
  const sourceChoices = options.actions.GET.source.choices.map(
    ([choice, label]) => ({ label, key: choice, value: choice })
  );
  return sourceChoices.filter(({ key }) => key !== 'file');
};

const InventorySourceFormFields = ({
  source,
  sourceOptions,
  organizationId,
}) => {
  const {
    values,
    initialValues,
    resetForm,
    setFieldTouched,
    setFieldValue,
  } = useFormikContext();
  const [sourceField, sourceMeta] = useField({
    name: 'source',
    validate: required(t`Set a value for this field`),
  });
  const [
    executionEnvironmentField,
    executionEnvironmentMeta,
    executionEnvironmentHelpers,
  ] = useField('execution_environment');

  const resetSubFormFields = sourceType => {
    if (sourceType === initialValues.source) {
      resetForm({
        values: {
          ...initialValues,
          name: values.name,
          description: values.description,
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

  const handleExecutionEnvironmentUpdate = useCallback(
    value => {
      setFieldValue('execution_environment', value);
      setFieldTouched('execution_environment', true, false);
    },
    [setFieldValue, setFieldTouched]
  );

  return (
    <>
      <FormField
        id="name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <ExecutionEnvironmentLookup
        helperTextInvalid={executionEnvironmentMeta.error}
        isValid={
          !executionEnvironmentMeta.touched || !executionEnvironmentMeta.error
        }
        onBlur={() => executionEnvironmentHelpers.setTouched()}
        value={executionEnvironmentField.value}
        onChange={handleExecutionEnvironmentUpdate}
        globallyAvailable
        organizationId={organizationId}
      />
      <FormGroup
        fieldId="source"
        helperTextInvalid={sourceMeta.error}
        isRequired
        validated={
          !sourceMeta.touched || !sourceMeta.error ? 'default' : 'error'
        }
        label={t`Source`}
      >
        <AnsibleSelect
          {...sourceField}
          id="source"
          data={[
            {
              value: '',
              key: '',
              label: t`Choose a source`,
              isDisabled: true,
            },
            ...buildSourceChoiceOptions(sourceOptions),
          ]}
          onChange={(event, value) => {
            resetSubFormFields(value);
          }}
        />
      </FormGroup>
      {!['', 'custom'].includes(sourceField.value) && (
        <SubFormLayout>
          <Title size="md" headingLevel="h4">
            {t`Source details`}
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
                insights: (
                  <InsightsSubForm
                    autoPopulateCredential={
                      !source?.id || source?.source !== 'insights'
                    }
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
  onCancel,
  onSubmit,
  source,
  submitError = null,
  organizationId,
}) => {
  const initialValues = {
    credential: source?.summary_fields?.credential || null,
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
    execution_environment:
      source?.summary_fields?.execution_environment || null,
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
              source={source}
              sourceOptions={sourceOptions}
              organizationId={organizationId}
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

export default InventorySourceForm;
