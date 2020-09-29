import React, { Component, Fragment } from 'react';
import PropTypes from 'prop-types';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import {
  Card as PFCard,
  CardBody as PFCardBody,
  ExpandableSection as PFExpandable,
} from '@patternfly/react-core';
import getErrorMessage from './getErrorMessage';

const Card = styled(PFCard)`
  background-color: var(--pf-global--BackgroundColor--200);
  overflow-wrap: break-word;
`;

const CardBody = styled(PFCardBody)`
  max-height: 200px;
  overflow: scroll;
`;

const Expandable = styled(PFExpandable)`
  text-align: left;

  & .pf-c-expandable__toggle {
    padding-left: 10px;
    margin-left: 5px;
    margin-top: 10px;
    margin-bottom: 10px;
  }
`;

class ErrorDetail extends Component {
  constructor(props) {
    super(props);

    this.state = {
      isExpanded: false,
    };

    this.handleToggle = this.handleToggle.bind(this);
    this.renderNetworkError = this.renderNetworkError.bind(this);
    this.renderStack = this.renderStack.bind(this);
  }

  handleToggle() {
    const { isExpanded } = this.state;
    this.setState({ isExpanded: !isExpanded });
  }

  renderNetworkError() {
    const { error } = this.props;
    const { response } = error;
    const message = getErrorMessage(response);

    return (
      <Fragment>
        <CardBody>
          {response?.config?.method.toUpperCase()} {response?.config?.url}{' '}
          <strong>{response?.status}</strong>
        </CardBody>
        <CardBody>
          {Array.isArray(message) ? (
            <ul>
              {message.map(m =>
                typeof m === 'string' ? <li key={m}>{m}</li> : null
              )}
            </ul>
          ) : (
            message
          )}
        </CardBody>
      </Fragment>
    );
  }

  renderStack() {
    const { error } = this.props;
    return <CardBody>{error.stack}</CardBody>;
  }

  render() {
    const { isExpanded } = this.state;
    const { error, i18n } = this.props;

    return (
      <Expandable
        toggleText={i18n._(t`Details`)}
        onToggle={this.handleToggle}
        isExpanded={isExpanded}
      >
        <Card>
          {Object.prototype.hasOwnProperty.call(error, 'response')
            ? this.renderNetworkError()
            : this.renderStack()}
        </Card>
      </Expandable>
    );
  }
}

ErrorDetail.propTypes = {
  error: PropTypes.instanceOf(Error).isRequired,
};

export default withI18n()(ErrorDetail);
