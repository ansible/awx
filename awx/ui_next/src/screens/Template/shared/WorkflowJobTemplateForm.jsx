import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Formik, Field } from 'formik';

import { Form, FormGroup } from '@patternfly/react-core';
import { required } from '@util/validators';
import PropTypes from 'prop-types';

import FormRow from '@components/FormRow';
import FormField, { FieldTooltip } from '@components/FormField';
import OrganizationLookup from '@components/Lookup/OrganizationLookup';
import { InventoryLookup } from '@components/Lookup';
import { VariablesField } from '@components/CodeMirrorInput';
import FormActionGroup from '@components/FormActionGroup';
import ContentError from '@components/ContentError';
import LabelSelect from './LabelSelect';

function WorkflowJobTemplateForm({
  handleSubmit,
  handleCancel,
  i18n,
  template = {},
}) {
  const [contentError, setContentError] = useState(null);
  const [inventory, setInventory] = useState(
    template?.summary_fields?.inventory || null
  );
  const [organization, setOrganization] = useState(
    template?.summary_fields?.organization || null
  );

  if (contentError) {
    return <ContentError error={contentError} />;
  }
  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={{
        name: template.name || '',
        description: template.description || '',
        inventory: template.summary_fields?.inventory?.id || '',
        organization: template.summary_fields?.organization?.id || '',
        labels: template.summary_fields?.labels?.results || [],
        variables: template.variables || '---',
        limit: template.limit || '',
        scmBranch: template.scm_branch || '',
        ask_limit_on_launch: template.ask_limit_on_launch || false,
        ask_inventory_on_launch: template.ask_inventory_on_launch || false,
        ask_variables_on_launch: template.ask_variables_on_launch || false,
        ask_scm_branch_on_launch: template.ask_scm_branch_on_launch || false,
      }}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormRow>
            <FormField
              id="wfjt-name"
              name="name"
              type="text"
              label={i18n._(t`Name`)}
              validate={required(null, i18n)}
              isRequired
            />
            <FormField
              id="wfjt-description"
              name="description"
              type="text"
              label={i18n._(t`Description`)}
            />
            <Field
              id="wfjt-organization"
              label={i18n._(t`Organization`)}
              name="organization"
            >
              {({ form }) => (
                <OrganizationLookup
                  helperTextInvalid={form.errors.organization}
                  isValid={
                    !form.touched.organization || !form.errors.organization
                  }
                  onBlur={() => form.setFieldTouched('organization')}
                  onChange={value => {
                    form.setFieldValue('organization', value?.id || null);
                    setOrganization(value);
                  }}
                  value={organization}
                  touched={form.touched.organization}
                  error={form.errors.organization}
                />
              )}
            </Field>
          </FormRow>
          <FormRow>
            <Field name="inventory">
              {({ form }) => (
                <InventoryLookup
                  value={inventory}
                  onBlur={() => form.setFieldTouched('inventory')}
                  tooltip={i18n._(t`Select the inventory containing the hosts
                  you want this job to manage.`)}
                  isValid={!form.touched.inventory || !form.errors.inventory}
                  helperTextInvalid={form.errors.inventory}
                  onChange={value => {
                    form.setFieldValue('inventory', value?.id || null);
                    form.setFieldValue(
                      'organizationId',
                      value?.organization || null
                    );
                    setInventory(value);
                  }}
                  touched={form.touched.inventory}
                  error={form.errors.inventory}
                />
              )}
            </Field>
            <FormGroup
              fieldId="wfjt-limit"
              name="limit"
              label={i18n._(t`Limit`)}
            >
              <FieldTooltip
                content={i18n._(
                  t`Provide a host pattern to further constrain the list of hosts that will be managed or affected by the workflow. This limit is applied to all job template nodes that prompt for a limit. Refer to Ansible documentation for more information and examples on patterns.`
                )}
              />
              <FormField type="text" name="limit" id="wfjt-limit" label="" />
            </FormGroup>
            <FormField
              type="text"
              id="wfjt-scmBranch"
              label={i18n._(t`SCM Branch`)}
              name="scmBranch"
            />
          </FormRow>

          <FormRow>
            <Field name="labels">
              {({ field, form }) => (
                <FormGroup label={i18n._(t`Labels`)} fieldId="wfjt-labels">
                  <FieldTooltip
                    content={i18n._(t`Optional labels that describe this job template,
                    such as 'dev' or 'test'. Labels can be used to group and filter
                    job templates and completed jobs.`)}
                  />
                  <LabelSelect
                    value={field.value}
                    onChange={labels => form.setFieldValue('labels', labels)}
                    onError={() => setContentError()}
                  />
                </FormGroup>
              )}
            </Field>
          </FormRow>
          <FormRow>
            <VariablesField
              id="host-variables"
              name="variables"
              label={i18n._(t`Variables`)}
            />
          </FormRow>
          <FormActionGroup
            onCancel={handleCancel}
            onSubmit={formik.handleSubmit}
          />
        </Form>
      )}
    </Formik>
  );
}

WorkflowJobTemplateForm.propTypes = {
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
};
export default withI18n()(WorkflowJobTemplateForm);
