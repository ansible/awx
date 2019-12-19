import React from 'react';
import { withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import { PageSection, Card, CardHeader, Tooltip } from '@patternfly/react-core';

import { TeamsAPI } from '@api';
import { Config } from '@contexts/Config';
import { CardBody } from '@components/Card';
import CardCloseButton from '@components/CardCloseButton';

import TeamForm from '../shared/TeamForm';

class TeamAdd extends React.Component {
  constructor(props) {
    super(props);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.state = { error: '' };
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
                <TeamForm
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

export { TeamAdd as _TeamAdd };
export default withI18n()(withRouter(TeamAdd));
