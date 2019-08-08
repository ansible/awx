import React from 'react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { withI18n } from '@lingui/react';
import {
  Title,
  EmptyState as PFEmptyState,
  EmptyStateIcon,
  EmptyStateBody,
} from '@patternfly/react-core';
import { ExclamationTriangleIcon } from '@patternfly/react-icons';
import { RootAPI } from '@api';
import ErrorDetail from '@components/ErrorDetail';
import NotFoundError from './NotFoundError';

const EmptyState = styled(PFEmptyState)`
  width: var(--pf-c-empty-state--m-lg--MaxWidth);
`;

async function logout() {
  await RootAPI.logout();
  window.location.replace('/#/login');
}

class ContentError extends React.Component {
  render() {
    const { error, children, i18n } = this.props;
    if (error && error.response && error.response.status === 401) {
      if (!error.response.headers['session-timeout']) {
        logout();
        return null;
      }
    }
    if (error && error.response && error.response.status === 404) {
      return <NotFoundError error={error}>{children}</NotFoundError>;
    }
    return (
      <EmptyState>
        <EmptyStateIcon icon={ExclamationTriangleIcon} />
        <Title size="lg">{i18n._(t`Something went wrong...`)}</Title>
        <EmptyStateBody>
          {children ||
            i18n._(
              t`There was an error loading this content. Please reload the page.`
            )}
        </EmptyStateBody>
        {error && <ErrorDetail error={error} />}
      </EmptyState>
    );
  }
}

export { ContentError as _ContentError };
export default withI18n()(ContentError);
