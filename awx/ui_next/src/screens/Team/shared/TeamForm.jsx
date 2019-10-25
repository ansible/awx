import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { withRouter } from 'react-router-dom';
import { Formik } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Form } from '@patternfly/react-core';

import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { required } from '@util/validators';

class TeamForm extends Component {
  constructor(props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);

    this.state = {
      formIsValid: true,
    };
  }

  isEditingNewTeam() {
    const { team } = this.props;
    return !team.id;
  }

  handleSubmit(values) {
    const { handleSubmit } = this.props;

    handleSubmit(values);
  }

  render() {
    const { team, handleCancel, i18n } = this.props;
    const { formIsValid, error } = this.state;

    return (
      <Formik
        initialValues={{
          name: team.name,
          description: team.description,
        }}
        onSubmit={this.handleSubmit}
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
            </FormRow>
            <FormActionGroup
              onCancel={handleCancel}
              onSubmit={formik.handleSubmit}
              submitDisabled={!formIsValid}
            />
            {error ? <div>error</div> : null}
          </Form>
        )}
      />
    );
  }
}

FormField.propTypes = {
  label: PropTypes.oneOfType([PropTypes.object, PropTypes.string]).isRequired,
};

TeamForm.propTypes = {
  team: PropTypes.shape(),
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
};

TeamForm.defaultProps = {
  team: {
    name: '',
    description: '',
  },
};

export { TeamForm as _TeamForm };
export default withI18n()(withRouter(TeamForm));
