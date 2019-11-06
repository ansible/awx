import React, { Component } from 'react';
import PropTypes from 'prop-types';

import { withRouter } from 'react-router-dom';
import { Formik, Field } from 'formik';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { Form } from '@patternfly/react-core';

import FormRow from '@components/FormRow';
import FormField from '@components/FormField';
import FormActionGroup from '@components/FormActionGroup/FormActionGroup';
import { VariablesField } from '@components/CodeMirrorInput';
import { required } from '@util/validators';
import { InventoryLookup } from '@components/Lookup';

class HostForm extends Component {
  constructor(props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);

    this.state = {
      formIsValid: true,
      inventory: props.host.summary_fields.inventory,
    };
  }

  handleSubmit(values) {
    const { handleSubmit } = this.props;

    handleSubmit(values);
  }

  render() {
    const { host, handleCancel, i18n } = this.props;
    const { formIsValid, inventory, error } = this.state;

    const initialValues = !host.id
      ? {
          name: host.name,
          description: host.description,
          inventory: host.inventory || '',
          variables: host.variables,
        }
      : {
          name: host.name,
          description: host.description,
          variables: host.variables,
        };

    return (
      <Formik
        initialValues={initialValues}
        onSubmit={this.handleSubmit}
        render={formik => (
          <Form autoComplete="off" onSubmit={formik.handleSubmit}>
            <FormRow>
              <FormField
                id="host-name"
                name="name"
                type="text"
                label={i18n._(t`Name`)}
                validate={required(null, i18n)}
                isRequired
              />
              <FormField
                id="host-description"
                name="description"
                type="text"
                label={i18n._(t`Description`)}
              />
              {!host.id && (
                <Field
                  name="inventory"
                  validate={required(
                    i18n._(t`Select a value for this field`),
                    i18n
                  )}
                  render={({ form }) => (
                    <InventoryLookup
                      value={inventory}
                      onBlur={() => form.setFieldTouched('inventory')}
                      tooltip={i18n._(
                        t`Select the inventory that this host will belong to.`
                      )}
                      isValid={
                        !form.touched.inventory || !form.errors.inventory
                      }
                      helperTextInvalid={form.errors.inventory}
                      onChange={value => {
                        form.setFieldValue('inventory', value.id);
                        this.setState({ inventory: value });
                      }}
                      required
                      touched={form.touched.inventory}
                      error={form.errors.inventory}
                    />
                  )}
                />
              )}
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

HostForm.propTypes = {
  host: PropTypes.shape(),
  handleSubmit: PropTypes.func.isRequired,
  handleCancel: PropTypes.func.isRequired,
};

HostForm.defaultProps = {
  host: {
    name: '',
    description: '',
    inventory: undefined,
    variables: '---\n',
    summary_fields: {
      inventory: null,
    },
  },
};

export { HostForm as _HostForm };
export default withI18n()(withRouter(HostForm));
