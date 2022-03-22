import React, { useEffect } from 'react';
import 'styled-components/macro';
import { t } from '@lingui/macro';
import { SearchIcon } from '@patternfly/react-icons';
import ContentEmpty from 'components/ContentEmpty';

export default function EmptyOutput({
  hasQueryParams,
  isJobRunning,
  onUnmount,
}) {
  let title;
  let message;
  let icon;

  useEffect(() => onUnmount);

  if (hasQueryParams) {
    title = t`The search filter did not produce any results…`;
    message = t`Please try another search using the filter above`;
    icon = SearchIcon;
  } else if (isJobRunning) {
    title = t`Waiting for job output…`;
  } else {
    title = t`No output found for this job.`;
  }

  return (
    <ContentEmpty
      css="height: 100%"
      title={title}
      message={message}
      icon={icon}
    />
  );
}
