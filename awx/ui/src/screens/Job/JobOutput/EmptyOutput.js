import React, { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import 'styled-components/macro';
import { t } from '@lingui/macro';
import {
  SearchIcon,
  ExclamationCircleIcon as PFExclamationCircleIcon,
} from '@patternfly/react-icons';
import ContentEmpty from 'components/ContentEmpty';

import styled from 'styled-components';

const ExclamationCircleIcon = styled(PFExclamationCircleIcon)`
  color: var(--pf-global--danger-color--100);
`;

export default function EmptyOutput({
  hasQueryParams,
  isJobRunning,
  onUnmount,
  job,
}) {
  let title;
  let message;
  let icon;
  const { typeSegment, id } = useParams();

  useEffect(() => onUnmount);

  if (hasQueryParams) {
    title = t`The search filter did not produce any results…`;
    message = t`Please try another search using the filter above`;
    icon = SearchIcon;
  } else if (isJobRunning) {
    title = t`Waiting for job output…`;
  } else if (job.status === 'failed') {
    title = t`This job failed and has no output.`;
    message = (
      <>
        {t`Return to `}{' '}
        <Link to={`/jobs/${typeSegment}/${id}/details`}>{t`details.`}</Link>
        <br />
        {job.job_explanation && (
          <>
            {t`Failure Explanation:`} {`${job.job_explanation}`}
          </>
        )}
      </>
    );
    icon = ExclamationCircleIcon;
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
