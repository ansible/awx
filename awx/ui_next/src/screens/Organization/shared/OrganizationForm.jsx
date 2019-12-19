import React, { useContext, useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { QuestionCircleIcon } from '@patternfly/react-icons';
import { Tooltip, Form, FormGroup } from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { ConfigContext } from '@contexts/Config';
import AnsibleSelect from '@components/AnsibleSelect';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { InstanceGroupsLookup } from '@components/Lookup/';
import { getAddedAndRemoved } from '@util/lists';
import { required, minMaxValue } from '@util/validators';

function OrganizationForm({ organization, i18n, me, onCancel, onSubmit }) {
  const defaultVenv = {
    label: i18n._(t`Use Default Ansible Environment`),
    value: '/venv/ansible/',
    key: 'default',
  };
  const { custom_virtualenvs } = useContext(ConfigContext);
  const [contentError, setContentError] = useState(null);
  const [hasContentLoading, setHasContentLoading] = useState(true);
  const [initialInstanceGroups, setInitialInstanceGroups] = useState([]);
  const [instanceGroups, setInstanceGroups] = useState([]);

  const handleCancel = () => {
    onCancel();
  };

  const handleSubmit = values => {
    const { added, removed } = getAddedAndRemoved(
      initialInstanceGroups,
      instanceGroups
    );
    const addedIds = added.map(({ id }) => id);
    const removedIds = removed.map(({ id }) => id);
    if (
      typeof values.max_hosts !== 'number' ||
      values.max_hosts === 'undefined'
    ) {
      values.max_hosts = 0;
    }
    onSubmit(values, addedIds, removedIds);
  };

  useEffect(() => {
    (async () => {
      const { id } = organization;
      if (!id) {
        setHasContentLoading(false);
        return;
      }
      setContentError(null);
      setHasContentLoading(true);
      try {
        const {
          data: { results = [] },
        } = await OrganizationsAPI.readInstanceGroups(id);
        setInitialInstanceGroups(results);
        setInstanceGroups(results);
      } catch (error) {
        setContentError(error);
      } finally {
        setHasContentLoading(false);
      }
    })();
  }, [organization]);

  if (contentError) {
    return <ContentError error={contentError} />;
  }

  if (hasContentLoading) {
    return <ContentLoading />;
  }

  return (
    <Formik
      initialValues={{
        name: organization.name,
        description: organization.description,
        custom_virtualenv: organization.custom_virtualenv || '',
        max_hosts: organization.max_hosts || '0',
      }}
      onSubmit={handleSubmit}
      render={formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormRow>
            <FormField
              id="org-name"
              name="name"
              type="text"
              label={i18n._(t`Name`)}
              validate={required(null, i18n)}
              isRequired
            />
            <FormField
              id="org-description"
              name="description"
              type="text"
              label={i18n._(t`Description`)}
            />
            <FormField
              id="org-max_hosts"
              name="max_hosts"
              type="number"
              label={
                <>
                  {i18n._(t`Max Hosts`)}{' '}
                  <Tooltip
                    position="right"
                    content={i18n._(
                      t`The maximum number of hosts allowed to be managed by this organization.
                      Value defaults to 0 which means no limit. Refer to the Ansible
                      documentation for more details.`
                    )}
                  >
                    <QuestionCircleIcon />
                  </Tooltip>
                </>
              }
              validate={minMaxValue(0, Number.MAX_SAFE_INTEGER, i18n)}
              me={me || {}}
              isDisabled={!me.is_superuser}
            />
            {custom_virtualenvs && custom_virtualenvs.length > 1 && (
              <Field
                name="custom_virtualenv"
                render={({ field }) => (
                  <FormGroup
                    fieldId="org-custom-virtualenv"
                    label={i18n._(t`Ansible Environment`)}
                  >
                    <AnsibleSelect
                      id="org-custom-virtualenv"
                      data={[
                        defaultVenv,
                        ...custom_virtualenvs
                          .filter(value => value !== defaultVenv.value)
                          .map(value => ({ value, label: value, key: value })),
                      ]}
                      {...field}
                    />
                  </FormGroup>
                )}
              />
            )}
          </FormRow>
          <InstanceGroupsLookup
            value={instanceGroups}
            onChange={setInstanceGroups}
            tooltip={i18n._(
              t`Select the Instance Groups for this Organization to run on.`
            )}
          />
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </Form>
      )}
    />
  );
}

FormField.propTypes = {
  label: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
};

OrganizationForm.propTypes = {
  organization: PropTypes.shape(),
  onSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
};

OrganizationForm.defaultProps = {
  organization: {
    name: '',
    description: '',
    max_hosts: '0',
    custom_virtualenv: '',
  },
};

OrganizationForm.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationForm as _OrganizationForm };
export default withI18n()(withRouter(OrganizationForm));
