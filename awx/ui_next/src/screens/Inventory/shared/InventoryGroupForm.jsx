import React from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { Formik } from 'formik';
import { Form, Card } from '@patternfly/react-core';
import { t } from '@lingui/macro';

import { CardBody } from '@components/Card';
import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { VariablesField } from '@components/CodeMirrorInput';
import { required } from '@util/validators';

function InventoryGroupForm({
  i18n,
  error,
  group = {},
  handleSubmit,
  handleCancel,
}) {
  const initialValues = {
    name: group.name || '',
    description: group.description || '',
    variables: group.variables || '---',
  };

  return (
    <Card className="awx-c-card">
      <CardBody>
        <Formik
          initialValues={initialValues}
          onSubmit={handleSubmit}
          render={formik => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormRow css="grid-template-columns: repeat(auto-fit, minmax(300px, 500px));">
                <FormField
                  id="inventoryGroup-name"
                  name="name"
                  type="text"
                  label={i18n._(t`Name`)}
                  validate={required(null, i18n)}
                  isRequired
                />
                <FormField
                  id="inventoryGroup-description"
                  name="description"
                  type="text"
                  label={i18n._(t`Description`)}
                />
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
              {error ? <div>error</div> : null}
            </Form>
          )}
        />
      </CardBody>
    </Card>
  );
}

export default withI18n()(withRouter(InventoryGroupForm));
