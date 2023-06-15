import React, { useCallback, useEffect } from 'react';
import { t } from '@lingui/macro';
import { useHistory } from 'react-router-dom';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { CardBody } from 'components/Card';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { FormSubmitError } from 'components/FormField';
import { FormColumnLayout } from 'components/FormLayout';
import { useSettings } from 'contexts/Settings';
import useModal from 'hooks/useModal';
import useRequest from 'hooks/useRequest';
import { SettingsAPI } from 'api';
import { formatJson } from '../../shared/settingUtils';
import {
  BooleanField,
  InputField,
  ObjectField,
  RevertAllAlert,
  RevertFormActionGroup,
  ChoiceField,
} from '../../shared';

function JobsEdit() {
  const history = useHistory();
  const { isModalOpen, toggleModal, closeModal } = useModal();
  const { PUT: options } = useSettings();

  const {
    isLoading,
    error,
    request: fetchJobs,
    result: jobs,
  } = useRequest(
    useCallback(async () => {
      const { data } = await SettingsAPI.readCategory('jobs');
      const {
        EVENT_STDOUT_MAX_BYTES_DISPLAY,
        STDOUT_MAX_BYTES_DISPLAY,
        ...jobsData
      } = data;
      const mergedData = {};
      Object.keys(jobsData).forEach((key) => {
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
      async (values) => {
        await SettingsAPI.updateAll(values);
        history.push('/settings/jobs/details');
      },
      [history]
    ),
    null
  );

  const { error: revertError, request: revertAll } = useRequest(
    useCallback(async () => {
      await SettingsAPI.revertCategory('jobs');
    }, []),
    null
  );

  const handleSubmit = async (form) => {
    await submitForm({
      ...form,
      AD_HOC_COMMANDS: formatJson(form.AD_HOC_COMMANDS),
      AWX_ISOLATION_SHOW_PATHS: formatJson(form.AWX_ISOLATION_SHOW_PATHS),
      AWX_ANSIBLE_CALLBACK_PLUGINS: formatJson(
        form.AWX_ANSIBLE_CALLBACK_PLUGINS
      ),
      AWX_TASK_ENV: formatJson(form.AWX_TASK_ENV),
      GALAXY_TASK_ENV: formatJson(form.GALAXY_TASK_ENV),
      DEFAULT_CONTAINER_RUN_OPTIONS: formatJson(
        form.DEFAULT_CONTAINER_RUN_OPTIONS
      ),
    });
  };

  const handleRevertAll = async () => {
    await revertAll();

    closeModal();

    history.push('/settings/jobs/details');
  };

  const handleCancel = () => {
    history.push('/settings/jobs/details');
  };

  const initialValues = (fields) =>
    Object.keys(fields).reduce((acc, key) => {
      if (fields[key].type === 'list' || fields[key].type === 'nested object') {
        acc[key] = fields[key].value
          ? JSON.stringify(fields[key].value, null, 2)
          : null;
      } else {
        acc[key] = fields[key].value ?? '';
      }
      return acc;
    }, {});

  // We have to rebuild the ALLOW_JINJA_IN_EXTRA_VARS object because the default value
  // is 'template' but its label that comes from the api is 'Only On Job Template
  // Definitions'.  The problem is that this label does not match whats in the help
  // text, or what is rendered on the screen in the details, 'template' is what is
  // rendered in those locations. For consistency sake I have changed that label
  // value below.

  const jinja = {
    default: 'template',
    help_text: jobs?.ALLOW_JINJA_IN_EXTRA_VARS?.help_text,
    label: jobs?.ALLOW_JINJA_IN_EXTRA_VARS?.label,
  };
  jinja.choices = jobs?.ALLOW_JINJA_IN_EXTRA_VARS?.choices.map(
    ([value, label]) =>
      value === 'template' ? [value, t`Template`] : [value, label]
  );

  return (
    <CardBody>
      {isLoading && <ContentLoading />}
      {!isLoading && error && <ContentError error={error} />}
      {!isLoading && jobs && (
        <Formik initialValues={initialValues(jobs)} onSubmit={handleSubmit}>
          {(formik) => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <InputField
                  name="AWX_ISOLATION_BASE_PATH"
                  config={jobs.AWX_ISOLATION_BASE_PATH ?? null}
                  isRequired={Boolean(options?.AWX_ISOLATION_BASE_PATH)}
                />
                <InputField
                  name="SCHEDULE_MAX_JOBS"
                  config={jobs.SCHEDULE_MAX_JOBS ?? null}
                  type={options?.SCHEDULE_MAX_JOBS ? 'number' : undefined}
                  isRequired={Boolean(options?.SCHEDULE_MAX_JOBS)}
                />
                <InputField
                  name="AWX_RUNNER_KEEPALIVE_SECONDS"
                  config={jobs.AWX_RUNNER_KEEPALIVE_SECONDS}
                  type="number"
                />
                <InputField
                  name="DEFAULT_JOB_TIMEOUT"
                  config={jobs.DEFAULT_JOB_TIMEOUT}
                  type="number"
                />
                <InputField
                  name="DEFAULT_JOB_IDLE_TIMEOUT"
                  config={jobs.DEFAULT_JOB_IDLE_TIMEOUT}
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
                <ChoiceField name="ALLOW_JINJA_IN_EXTRA_VARS" config={jinja} />
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
                  name="AWX_MOUNT_ISOLATED_PATHS_ON_K8S"
                  config={jobs.AWX_MOUNT_ISOLATED_PATHS_ON_K8S}
                />
                <ObjectField
                  name="AD_HOC_COMMANDS"
                  config={jobs.AD_HOC_COMMANDS}
                />
                <ObjectField
                  name="DEFAULT_CONTAINER_RUN_OPTIONS"
                  config={jobs.DEFAULT_CONTAINER_RUN_OPTIONS}
                />
                <ObjectField
                  name="AWX_ANSIBLE_CALLBACK_PLUGINS"
                  config={jobs.AWX_ANSIBLE_CALLBACK_PLUGINS}
                />
                <ObjectField
                  name="AWX_ISOLATION_SHOW_PATHS"
                  config={jobs.AWX_ISOLATION_SHOW_PATHS}
                />
                <ObjectField name="AWX_TASK_ENV" config={jobs.AWX_TASK_ENV} />
                <ObjectField
                  name="GALAXY_TASK_ENV"
                  config={jobs.GALAXY_TASK_ENV}
                />
                {submitError && <FormSubmitError error={submitError} />}
                {revertError && <FormSubmitError error={revertError} />}
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
          )}
        </Formik>
      )}
    </CardBody>
  );
}

export default JobsEdit;
