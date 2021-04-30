import React, { useCallback, useState } from 'react';
import PropTypes from 'prop-types';

import { t } from '@lingui/macro';
import { Formik, useField, useFormikContext } from 'formik';
import { Form } from '@patternfly/react-core';
import FormActionGroup from '../../../components/FormActionGroup/FormActionGroup';
import FormField, { FormSubmitError } from '../../../components/FormField';
import OrganizationLookup from '../../../components/Lookup/OrganizationLookup';
import { required } from '../../../util/validators';
import { FormColumnLayout } from '../../../components/FormLayout';

function TeamFormFields({ team }) {
  const { setFieldValue } = useFormikContext();
  const [organization, setOrganization] = useState(
    team.summary_fields ? team.summary_fields.organization : null
  );
  const [, orgMeta, orgHelpers] = useField({
    name: 'organization',
    validate: required(t`Select a value for this field`),
  });

  const onOrganizationChange = useCallback(
    value => {
      setFieldValue('organization', value.id);
      setOrganization(value);
    },
    [setFieldValue]
  );

  return (
    <>
      <FormField
        id="team-name"
        label={t`Name`}
        name="name"
        type="text"
        validate={required(null)}
        isRequired
      />
      <FormField
        id="team-description"
        label={t`Description`}
        name="description"
        type="text"
      />
      <OrganizationLookup
        helperTextInvalid={orgMeta.error}
        isValid={!orgMeta.touched || !orgMeta.error}
        onBlur={() => orgHelpers.setTouched('organization')}
        onChange={onOrganizationChange}
        value={organization}
        required
        autoPopulate={!team?.id}
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

export default TeamForm;
