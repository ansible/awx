import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { Formik, useField } from 'formik';
import { Form } from '@patternfly/react-core';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { required } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';

function TeamFormFields(props) {
  const { team, i18n } = props;
  const [organization, setOrganization] = useState(
    team.summary_fields ? team.summary_fields.organization : null
  );
  const orgFieldArr = useField({
    name: 'organization',
    validate: required(i18n._(t`Select a value for this field`), i18n),
  });
  const orgMeta = orgFieldArr[1];
  const orgHelpers = orgFieldArr[2];

  return (
    <>
      <FormField
        id="team-name"
        label={i18n._(t`Name`)}
        name="name"
        type="text"
        validate={required(null, i18n)}
        isRequired
      />
      <FormField
        id="team-description"
        label={i18n._(t`Description`)}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched('organization')}
        onChange={value => {
          orgHelpers.setValue(value.id);
          setOrganization(value);
        }}
        value={organization}
        required
      />
    </>
  );
}

function TeamForm(props) {
  const { team, handleCancel, handleSubmit, submitError, ...rest } = props;

  return (
    <Formik
      initialValues={{
        description: team.description || '',
        name: team.name || '',
        organization: team.organization || '',
      }}
      onSubmit={handleSubmit}
    >
      {formik => (
        <Form autoComplete="off" onSubmit={formik.handleSubmit}>
          <FormColumnLayout>
            <TeamFormFields team={team} {...rest} />
            <FormSubmitError error={submitError} />
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={formik.handleSubmit}
            />
          </FormColumnLayout>
        </Form>
      )}
    </Formik>
  );
}

TeamForm.propTypes = {
  handleCancel: PropTypes.func.isRequired,
  handleSubmit: PropTypes.func.isRequired,
  team: PropTypes.shape({}),
  submitError: PropTypes.shape(),
};

TeamForm.defaultProps = {
  team: {},
  submitError: null,
};

export default withI18n()(TeamForm);
