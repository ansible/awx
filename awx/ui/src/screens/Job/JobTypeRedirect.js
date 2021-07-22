import React, { useCallback, useEffect } from 'react';
import { Redirect, Link } from 'react-router-dom';
import { PageSection, Card } from '@patternfly/react-core';

import { t } from '@lingui/macro';
import useRequest from 'hooks/useRequest';
import { UnifiedJobsAPI } from 'api';
import ContentError from 'components/ContentError';
import ContentLoading from 'components/ContentLoading';
import { JOB_TYPE_URL_SEGMENTS } from '../../constants';

const NOT_FOUND = 'not found';

function JobTypeRedirect({ id, path, view }) {
  const {
    isLoading,
    error,
    result: { job },
    request: loadJob,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { results },
      } = await UnifiedJobsAPI.read({ id });
      const [item] = results;
      return { job: item };
    }, [id]),
    { job: {} }
  );
  useEffect(() => {
    loadJob();
  }, [loadJob]);

  if (error) {
    return (
      <PageSection>
        <Card>
          {error === NOT_FOUND ? (
            <ContentError isNotFound>
              <Link to="/jobs">{t`View all Jobs`}</Link>
            </ContentError>
          ) : (
            <ContentError error={error} />
          )}
        </Card>
      </PageSection>
    );
  }
  if (isLoading || !job?.id) {
    return (
      <PageSection>
        <Card>
          <ContentLoading />
        </Card>
      </PageSection>
    );
  }
  const typeSegment = JOB_TYPE_URL_SEGMENTS[job.type];
  return <Redirect from={path} to={`/jobs/${typeSegment}/${job.id}/${view}`} />;
}

JobTypeRedirect.defaultProps = {
  view: 'output',
};
export default JobTypeRedirect;
