import React from 'react';
import { withRouter } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';

import { TeamsAPI } from '../../../api';
import { Config } from '../../../contexts/Config';
import { CardBody } from '../../../components/Card';
import TeamForm from '../shared/TeamForm';

class TeamAdd extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.state = { error: null };
  }

  async handleSubmit(values) {
    const { history } = this.props;
    try {
      const { data: response } = await TeamsAPI.create(values);
      history.push(`/teams/${response.id}`);
    } catch (error) {
      this.setState({ error });
    }
  }

  handleCancel() {
    const { history } = this.props;
    history.push('/teams');
  }

  render() {
    const { error } = this.state;

    return (
      <PageSection>
        <Card>
          <CardBody>
            <Config>
              {({ me }) => (
                <TeamForm
                  handleSubmit={this.handleSubmit}
                  handleCancel={this.handleCancel}
                  me={me || {}}
                  submitError={error}
                />
              )}
            </Config>
          </CardBody>
        </Card>
      </PageSection>
    );
  }
}

export { TeamAdd as _TeamAdd };
export default withRouter(TeamAdd);
