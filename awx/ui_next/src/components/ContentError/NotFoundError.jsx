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
import ErrorDetail from '@components/ErrorDetail';

const EmptyState = styled(PFEmptyState)`
  width: var(--pf-c-empty-state--m-lg--MaxWidth);
`;

function NotFoundError({ i18n, error, children }) {
  return (
    <EmptyState>
      <EmptyStateIcon icon={ExclamationTriangleIcon} />
      <Title size="lg">{i18n._(t`Not Found`)}</Title>
      <EmptyStateBody>
        {children || i18n._(`The page you requested could not be found.`)}
      </EmptyStateBody>
      {error && <ErrorDetail error={error} />}
    </EmptyState>
  );
}

export { NotFoundError as _NotFoundError };
export default withI18n()(NotFoundError);
