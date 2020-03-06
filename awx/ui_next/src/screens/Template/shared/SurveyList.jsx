import React, { useEffect, useCallback } from 'react';
import { withI18n } from '@lingui/react';

import useRequest from '@util/useRequest';
import ContentError from '@components/ContentError';
import ContentLoading from '@components/ContentLoading';
import { JobTemplatesAPI } from '@api';
import SurveyListItem from './SurveyListItem';

function SurveyList({ template }) {
  const {
    result: questions,
    error: contentError,
    isLoading,
    request: fetchSurvey,
  } = useRequest(
    useCallback(async () => {
      const {
        data: { spec },
      } = await JobTemplatesAPI.readSurvey(template.id);

      return spec.map((s, index) => ({ ...s, id: index }));
    }, [template.id])
  );

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);
  if (contentError) {
    return <ContentError error={contentError} />;
  }
  if (isLoading) {
    return <ContentLoading />;
  }

  return (
    questions?.length > 0 &&
    questions.map((question, index) => (
      <SurveyListItem
        key={question.id}
        isLast={index === questions.length - 1}
        isFirst={index === 0}
        question={question}
      />
    ))
  );
}
export default withI18n()(SurveyList);
