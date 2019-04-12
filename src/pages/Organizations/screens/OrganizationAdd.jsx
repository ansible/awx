import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  PageSection,
  Card,
  CardHeader,
  CardBody,
  Button,
  Tooltip,
} from '@patternfly/react-core';
import { TimesIcon } from '@patternfly/react-icons';

import { withNetwork } from '../../../contexts/Network';

import OrganizationForm from '../components/OrganizationForm';

class OrganizationAdd extends React.Component {
  constructor (props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      error: '',
    };
  }

  async handleSubmit (values, groupsToAssociate) {
    const { api, handleHttpError } = this.props;
    try {
      const { data: response } = await api.createOrganization(values);
      const instanceGroupsUrl = response.related.instance_groups;
      try {
        await Promise.all(groupsToAssociate.map(id => api
          .associateInstanceGroup(instanceGroupsUrl, id)));
        this.handleSuccess(response.id);
      } catch (err) {
        handleHttpError(err) || this.setState({ error: err });
      }
    } catch (err) {
      this.setState({ error: err });
    }
  }

  handleCancel () {
    const { history } = this.props;
    history.push('/organizations');
  }

  handleSuccess (id) {
    const { history } = this.props;
    history.push(`/organizations/${id}`);
  }

  render () {
    const { error } = this.state;

    return (
      <PageSection>
        <I18n>
          {({ i18n }) => (
            <Card>
              <CardHeader className="at-u-textRight">
                <Tooltip
                  content={i18n._(t`Close`)}
                  position="top"
                >
                  <Button
                    variant="plain"
                    aria-label={i18n._(t`Close`)}
                    onClick={this.handleCancel}
                  >
                    <TimesIcon />
                  </Button>
                </Tooltip>
              </CardHeader>
              <CardBody>
                <OrganizationForm
                  handleSubmit={this.handleSubmit}
                  handleCancel={this.handleCancel}
                />
                {error ? <div>error</div> : ''}
              </CardBody>
            </Card>
          )}
        </I18n>
      </PageSection>
    );
  }
}

OrganizationAdd.propTypes = {
  api: PropTypes.shape().isRequired,
};

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string)
};

export { OrganizationAdd as _OrganizationAdd };
export default withNetwork(withRouter(OrganizationAdd));
