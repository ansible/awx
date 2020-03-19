import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { CardBody } from '@components/Card';
import SurveyQuestionForm from './SurveyQuestionForm';

export default function SurveyQuestionAdd({ survey, updateSurvey }) {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const match = useRouteMatch();

  const handleSubmit = async question => {
    if (survey.spec.find(q => q.variable === question.variable)) {
      setFormError(
        new Error(
          `Survey already contains a question with variable named “${question.variable}”`
        )
      );
      return;
    }
    try {
      await updateSurvey(survey.spec.concat(question));
      history.push(match.url.replace('/add', ''));
    } catch (err) {
      setFormError(err);
    }
  };

  const handleCancel = () => {
    history.push(match.url.replace('/add', ''));
  };

  return (
    <CardBody>
      <SurveyQuestionForm
        handleSubmit={handleSubmit}
        handleCancel={handleCancel}
        submitError={formError}
      />
    </CardBody>
  );
}
