import React, { useState } from 'react';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import { Formik } from 'formik';
import { Form } from '@patternfly/react-core';
import { useHistory } from 'react-router-dom';
import { SystemJobTemplatesAPI } from '../../../api';
import FormField, { FormSubmitError } from '../../../components/FormField';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import { FormColumnLayout } from '../../../components/FormLayout';
import { minMaxValue } from '../../../util/validators';

import { CardBody } from '../../../components/Card';

function ManagementJobEdit({ i18n, managementJob }) {
  const history = useHistory();
  const [formError, setFormError] = useState(null);

  const handleCancel = () => {
    history.push(`/management_jobs/${managementJob?.id}/details`);
  };

  const handleSubmit = async values => {
    try {
      await SystemJobTemplatesAPI.update(managementJob?.id, {
        default_days: values.dataRetention,
      });
      history.push(`/management_jobs/${managementJob?.id}/details`);
    } catch (error) {
      setFormError(error);
    }
  };

  return (
    <CardBody>
      {managementJob?.default_days ? (
        <Formik
          initialValues={{
            dataRetention: managementJob?.default_days || null,
            description: i18n._(t`Delete data older than this number of days.`),
          }}
          onSubmit={handleSubmit}
        >
          {formik => (
            <Form autoComplete="off" onSubmit={formik.handleSubmit}>
              <FormColumnLayout>
                <FormField
                  id="data-retention"
                  name="dataRetention"
                  type="number"
                  label={i18n._(t`Data Retention (Days)`)}
                  tooltip={i18n._(
                    t`Delete data older than this number of days.`
                  )}
                  validate={minMaxValue(0, Number.MAX_SAFE_INTEGER, i18n)}
                />
                <FormSubmitError error={formError} />
                <FormActionGroup
                  onCancel={handleCancel}
                  onSubmit={formik.handleSubmit}
                />
              </FormColumnLayout>
            </Form>
          )}
        </Formik>
      ) : null}
    </CardBody>
  );
}

export default withI18n()(ManagementJobEdit);
