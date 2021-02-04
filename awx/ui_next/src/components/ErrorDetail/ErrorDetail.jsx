import React, { useState, Fragment } from 'react';
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

function ErrorDetail({ error, i18n }) {
  const { response } = error;
  const [isExpanded, setIsExpanded] = useState(false);

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
  };

  const renderNetworkError = () => {
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
  };

  const renderStack = () => {
    return <CardBody>{error.stack}</CardBody>;
  };

  return (
    <Expandable
      toggleText={i18n._(t`Details`)}
      onToggle={handleToggle}
      isExpanded={isExpanded}
    >
      <Card>
        {Object.prototype.hasOwnProperty.call(error, 'response')
          ? renderNetworkError()
          : renderStack()}
      </Card>
    </Expandable>
  );
}

ErrorDetail.propTypes = {
  error: PropTypes.instanceOf(Error).isRequired,
};

export default withI18n()(ErrorDetail);
