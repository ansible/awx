import React, { Component } from 'react';
import PropTypes from 'prop-types';
import { withRouter } from 'react-router-dom';
import { CardBody } from '@components/Card';

import { HostsAPI } from '@api';
import { Config } from '@contexts/Config';

import HostForm from '../shared';

class HostEdit extends Component {
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
    const { host } = this.props;
    try {
      await HostsAPI.update(host.id, values);
      this.handleSuccess();
    } catch (err) {
      this.setState({ error: err });
    }
  }

  handleCancel() {
    const {
      host: { id },
      history,
    } = this.props;
    history.push(`/hosts/${id}/details`);
  }

  handleSuccess() {
    const {
      host: { id },
      history,
    } = this.props;
    history.push(`/hosts/${id}/details`);
  }

  render() {
    const { host } = this.props;
    const { error } = this.state;

    return (
      <CardBody>
        <Config>
          {({ me }) => (
            <HostForm
              host={host}
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

HostEdit.propTypes = {
  host: PropTypes.shape().isRequired,
};

export { HostEdit as _HostEdit };
export default withRouter(HostEdit);
