import React from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  PageSection,
  Card,
  CardHeader,
  CardBody,
  Tooltip,
} from '@patternfly/react-core';

import { OrganizationsAPI } from '@api';
import { Config } from '@contexts/Config';
import CardCloseButton from '@components/CardCloseButton';

import OrganizationForm from '../shared/OrganizationForm';

class OrganizationAdd extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.state = { error: '' };
  }

  async handleSubmit(values, groupsToAssociate) {
    const { history } = this.props;
    try {
      const { data: response } = await OrganizationsAPI.create(values);
      await Promise.all(
        groupsToAssociate.map(id =>
          OrganizationsAPI.associateInstanceGroup(response.id, id)
        )
      );
      history.push(`/organizations/${response.id}`);
    } catch (error) {
      this.setState({ error });
    }
  }

  handleCancel() {
    const { history } = this.props;
    history.push('/organizations');
  }

  render() {
    const { error } = this.state;
    const { i18n } = this.props;

    return (
      <PageSection>
        <Card>
          <CardHeader className="at-u-textRight">
            <Tooltip content={i18n._(t`Close`)} position="top">
              <CardCloseButton onClick={this.handleCancel} />
            </Tooltip>
          </CardHeader>
          <CardBody>
            <Config>
              {({ me }) => (
                <OrganizationForm
                  handleSubmit={this.handleSubmit}
                  handleCancel={this.handleCancel}
                  me={me || {}}
                />
              )}
            </Config>
            {error ? <div>error</div> : ''}
          </CardBody>
        </Card>
      </PageSection>
    );
  }
}

OrganizationAdd.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { OrganizationAdd as _OrganizationAdd };
export default withI18n()(withRouter(OrganizationAdd));
