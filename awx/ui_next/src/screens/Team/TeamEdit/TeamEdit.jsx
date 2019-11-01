import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { CardBody } from '@patternfly/react-core';

import { TeamsAPI } from '@api';
import { Config } from '@contexts/Config';

import TeamForm from '../shared/TeamForm';

class TeamEdit extends Component {
  constructor(props) {
    super(props);

    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleCancel = this.handleCancel.bind(this);
    this.handleSuccess = this.handleSuccess.bind(this);

    this.state = {
      error: '',
    };
  }

  async handleSubmit(values) {
    const { team } = this.props;
    try {
      await TeamsAPI.update(team.id, values);
      this.handleSuccess();
    } catch (err) {
      this.setState({ error: err });
    }
  }

  handleCancel() {
    const {
      team: { id },
      history,
    } = this.props;
    history.push(`/teams/${id}/details`);
  }

  handleSuccess() {
    const {
      team: { id },
      history,
    } = this.props;
    history.push(`/teams/${id}/details`);
  }

  render() {
    const { team } = this.props;
    const { error } = this.state;

    return (
      <CardBody>
        <Config>
          {({ me }) => (
            <TeamForm
              team={team}
              handleSubmit={this.handleSubmit}
              handleCancel={this.handleCancel}
              me={me || {}}
            />
          )}
        </Config>
        {error ? <div>error</div> : null}
      </CardBody>
    );
  }
}

TeamEdit.propTypes = {
  team: PropTypes.shape().isRequired,
};

TeamEdit.contextTypes = {
  custom_virtualenvs: PropTypes.arrayOf(PropTypes.string),
};

export { TeamEdit as _TeamEdit };
export default withRouter(TeamEdit);
