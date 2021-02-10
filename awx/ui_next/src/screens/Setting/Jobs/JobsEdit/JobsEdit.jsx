import React, { useCallback, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { CardBody } from '../../../../components/Card';
import ContentError from '../../../../components/ContentError';
import ContentLoading from '../../../../components/ContentLoading';
import { FormSubmitError } from '../../../../components/FormField';
import { FormColumnLayout } from '../../../../components/FormLayout';
import { useSettings } from '../../../../contexts/Settings';
import {
  BooleanField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
} from '../../shared';
import useModal from '../../../../util/useModal';
import useRequest from '../../../../util/useRequest';
import { formatJson } from '../../shared/settingUtils';
import { SettingsAPI } from '../../../../api';

function JobsEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const { isLoading, error, request: fetchJobs, result: jobs } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('jobs');
      const {
        ALLOW_JINJA_IN_EXTRA_VARS,
        AWX_ISOLATED_KEY_GENERATION,
        AWX_ISOLATED_PRIVATE_KEY,
        AWX_ISOLATED_PUBLIC_KEY,
        EVENT_STDOUT_MAX_BYTES_DISPLAY,
        STDOUT_MAX_BYTES_DISPLAY,
        ...jobsData
      } = data;
      const mergedData = {};
      Object.keys(jobsData).forEach(key => {
        if (!options[key]) {
          return;
        }
        mergedData[key] = options[key];
        mergedData[key].value = jobsData[key];
      });

      return mergedData;
    }, [options]),
    null
  );

  useEffect(() => {
    fetchJobs();
  }, [fetchJobs]);

  const { error: submitError, request: submitForm } = useRequest(
    useCallback(
      async values => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/jobs/details');
      },
      [history]
    ),
    null
  );

  const handleSubmit = async form => {
    await submitForm({
      ...form,
      AD_HOC_COMMANDS: formatJson(form.AD_HOC_COMMANDS),
      AWX_PROOT_SHOW_PATHS: formatJson(form.AWX_PROOT_SHOW_PATHS),
      AWX_PROOT_HIDE_PATHS: formatJson(form.AWX_PROOT_HIDE_PATHS),
      AWX_ANSIBLE_CALLBACK_PLUGINS: formatJson(
        form.AWX_ANSIBLE_CALLBACK_PLUGINS
      ),
      AWX_TASK_ENV: formatJson(form.AWX_TASK_ENV),
    });
  };

  const handleRevertAll = async () => {
    const defaultValues = {};
    Object.entries(jobs).forEach(([key, value]) => {
      defaultValues[key] = value.default;
    });
    await submitForm(defaultValues);
    closeModal();
  };

  const handleCancel = () => {
    history.push('/settings/jobs/details');
  };

  const initialValues = fields =>
    Object.keys(fields).reduce((acc, key) => {
      if (fields[key].type === 'list' || fields[key].type === 'nested object') {
        const emptyDefault = fields[key].type === 'list' ? '[]' : '{}';
        acc[key] = fields[key].value
          ? JSON.stringify(fields[key].value, null, 2)
          : emptyDefault;
      } else {
        acc[key] = fields[key].value ?? '';
      }
      return acc;
    }, {});

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && jobs && (
        <Formik initialValues={initialValues(jobs)} onSubmit={handleSubmit}>
          {formik => {
            return (
              <Form autoComplete="off" onSubmit={formik.handleSubmit}>
                <FormColumnLayout>
                  <InputField
                    name="AWX_PROOT_BASE_PATH"
                    config={jobs.AWX_PROOT_BASE_PATH}
                    isRequired
                  />
                  <InputField
                    name="SCHEDULE_MAX_JOBS"
                    config={jobs.SCHEDULE_MAX_JOBS}
                    type="number"
                    isRequired
                  />
                  <InputField
                    name="DEFAULT_JOB_TIMEOUT"
                    config={jobs.DEFAULT_JOB_TIMEOUT}
                    type="number"
                  />
                  <InputField
                    name="DEFAULT_INVENTORY_UPDATE_TIMEOUT"
                    config={jobs.DEFAULT_INVENTORY_UPDATE_TIMEOUT}
                    type="number"
                  />
                  <InputField
                    name="DEFAULT_PROJECT_UPDATE_TIMEOUT"
                    config={jobs.DEFAULT_PROJECT_UPDATE_TIMEOUT}
                    type="number"
                  />
                  <InputField
                    name="ANSIBLE_FACT_CACHE_TIMEOUT"
                    config={jobs.ANSIBLE_FACT_CACHE_TIMEOUT}
                    type="number"
                  />
                  <InputField
                    name="MAX_FORKS"
                    config={jobs.MAX_FORKS}
                    type="number"
                  />
                  <BooleanField
                    name="AWX_PROOT_ENABLED"
                    config={jobs.AWX_PROOT_ENABLED}
                  />
                  <BooleanField
                    name="PROJECT_UPDATE_VVV"
                    config={jobs.PROJECT_UPDATE_VVV}
                  />
                  <BooleanField
                    name="GALAXY_IGNORE_CERTS"
                    config={jobs.GALAXY_IGNORE_CERTS}
                  />
                  <BooleanField
                    name="AWX_ROLES_ENABLED"
                    config={jobs.AWX_ROLES_ENABLED}
                  />
                  <BooleanField
                    name="AWX_COLLECTIONS_ENABLED"
                    config={jobs.AWX_COLLECTIONS_ENABLED}
                  />
                  <BooleanField
                    name="AWX_SHOW_PLAYBOOK_LINKS"
                    config={jobs.AWX_SHOW_PLAYBOOK_LINKS}
                  />
                  <BooleanField
                    name="AWX_ISOLATED_HOST_KEY_CHECKING"
                    config={jobs.AWX_ISOLATED_HOST_KEY_CHECKING}
                  />
                  <BooleanField
                    name="AWX_RESOURCE_PROFILING_ENABLED"
                    config={jobs.AWX_RESOURCE_PROFILING_ENABLED}
                  />
                  <InputField
                    name="AWX_ISOLATED_CHECK_INTERVAL"
                    config={jobs.AWX_ISOLATED_CHECK_INTERVAL}
                    type="number"
                    isRequired
                  />
                  <InputField
                    name="AWX_ISOLATED_LAUNCH_TIMEOUT"
                    config={jobs.AWX_ISOLATED_LAUNCH_TIMEOUT}
                    type="number"
                    isRequired
                  />
                  <InputField
                    name="AWX_ISOLATED_CONNECTION_TIMEOUT"
                    config={jobs.AWX_ISOLATED_CONNECTION_TIMEOUT}
                    type="number"
                  />
                  <ObjectField
                    name="AD_HOC_COMMANDS"
                    config={jobs.AD_HOC_COMMANDS}
                  />
                  <ObjectField
                    name="AWX_ANSIBLE_CALLBACK_PLUGINS"
                    config={jobs.AWX_ANSIBLE_CALLBACK_PLUGINS}
                  />
                  <ObjectField
                    name="AWX_PROOT_SHOW_PATHS"
                    config={jobs.AWX_PROOT_SHOW_PATHS}
                  />
                  <ObjectField
                    name="AWX_PROOT_HIDE_PATHS"
                    config={jobs.AWX_PROOT_HIDE_PATHS}
                  />
                  <ObjectField name="AWX_TASK_ENV" config={jobs.AWX_TASK_ENV} />
                  {submitError && <FormSubmitError error={submitError} />}
                </FormColumnLayout>
                <RevertFormActionGroup
                  onCancel={handleCancel}
                  onSubmit={formik.handleSubmit}
                  onRevert={toggleModal}
                />
                {isModalOpen && (
                  <RevertAllAlert
                    onClose={closeModal}
                    onRevertAll={handleRevertAll}
                  />
                )}
              </Form>
            );
          }}
        </Formik>
      )}
    </CardBody>
  );
}

export default JobsEdit;
