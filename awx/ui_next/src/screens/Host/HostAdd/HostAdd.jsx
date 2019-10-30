import React from 'react';
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

import { HostsAPI } from '@api';
import { Config } from '@contexts/Config';
import CardCloseButton from '@components/CardCloseButton';

import HostForm from '../shared/HostForm';

class HostAdd extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.state = { error: '' };
  }

  async handleSubmit(values) {
    const { history } = this.props;
    try {
      const { data: response } = await HostsAPI.create(values);
      history.push(`/hosts/${response.id}`);
    } catch (error) {
      this.setState({ error });
    }
  }

  handleCancel() {
    const { history } = this.props;
    history.push('/hosts');
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
                <HostForm
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

export { HostAdd as _HostAdd };
export default withI18n()(withRouter(HostAdd));
