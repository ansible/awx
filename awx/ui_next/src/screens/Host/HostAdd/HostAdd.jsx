import React from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { PageSection, Card } from '@patternfly/react-core';
import { CardBody } from '@components/Card';
import { HostsAPI } from '@api';
import { Config } from '@contexts/Config';
import HostForm from '../shared';

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

    return (
      <PageSection>
        <Card>
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
