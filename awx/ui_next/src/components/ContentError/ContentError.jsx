import React, { Fragment } from 'react';
import { Link, Redirect } from 'react-router-dom';
import { bool, instanceOf } from 'prop-types';
import { t } from '@lingui/macro';
import { withI18n } from '@lingui/react';
import {
  Title,
  EmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { ExclamationTriangleIcon } from '@patternfly/react-icons';
import { RootAPI } from '../../api';
import ErrorDetail from '../ErrorDetail';

async function logout() {
  await RootAPI.logout();
  window.location.replace('/#/login');
}

function ContentError({ error, children, isNotFound, i18n }) {
  if (error && error.response && error.response.status === 401) {
    if (!error.response.headers['session-timeout']) {
      logout();
      return null;
    }
  }
  const is404 =
    isNotFound || (error && error.response && error.response.status === 404);
  const is401 = error && error.response && error.response.status === 401;
  return (
    <Fragment>
      {is401 ? (
        <Redirect to="/login" />
      ) : (
        <EmptyState variant="full">
          <EmptyStateIcon icon={ExclamationTriangleIcon} />
          <Title size="lg" headingLevel="h3">
            {is404 ? i18n._(t`Not Found`) : i18n._(t`Something went wrong...`)}
          </Title>
          <EmptyStateBody>
            {is404
              ? i18n._(t`The page you requested could not be found.`)
              : i18n._(
                  t`There was an error loading this content. Please reload the page.`
                )}{' '}
            {children || (
              <Link to="/home">{i18n._(t`Back to Dashboard.`)}</Link>
            )}
          </EmptyStateBody>
          {error && <ErrorDetail error={error} />}
        </EmptyState>
      )}
    </Fragment>
  );
}
ContentError.propTypes = {
  error: instanceOf(Error),
  isNotFound: bool,
};
ContentError.defaultProps = {
  error: null,
  isNotFound: false,
};

export { ContentError as _ContentError };
export default withI18n()(ContentError);
