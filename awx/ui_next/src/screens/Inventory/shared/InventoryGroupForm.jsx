import React from 'react';
import { withI18n } from '@lingui/react';
import { Formik } from 'formik';
import { Form, Card } from '@patternfly/react-core';
import { t } from '@lingui/macro';

import { CardBody } from '../../../components/Card';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import { VariablesField } from '../../../components/CodeMirrorInput';
import { required } from '../../../util/validators';
import {
  FormColumnLayout,
  FormFullWidthLayout,
} from '../../../components/FormLayout';

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
    <Card>
      <CardBody>
        <Formik initialValues={initialValues} onSubmit={handleSubmit}>
          {formik => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
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
                <FormFullWidthLayout>
                  <VariablesField
                    id="host-variables"
                    name="variables"
                    label={i18n._(t`Variables`)}
                  />
                </FormFullWidthLayout>
                <FormActionGroup
                  onCancel={handleCancel}
                  onSubmit={formik.handleSubmit}
                />
                {error && <FormSubmitError error={error} />}
              </FormColumnLayout>
            </Form>
          )}
        </Formik>
      </CardBody>
    </Card>
  );
}

export default withI18n()(InventoryGroupForm);
