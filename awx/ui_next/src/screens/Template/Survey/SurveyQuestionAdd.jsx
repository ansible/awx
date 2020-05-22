import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import { CardBody } from '../../../components/Card';
import SurveyQuestionForm from './SurveyQuestionForm';

export default function SurveyQuestionAdd({ survey, updateSurvey }) {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const match = useRouteMatch();

  const handleSubmit = async question => {
    try {
      if (survey.spec?.some(q => q.variable === question.variable)) {
        setFormError(
          new Error(
            `Survey already contains a question with variable named “${question.variable}”`
          )
        );
        return;
      }
      if (question.type === 'multiselect') {
        question.default = question.default
          .split('\n')
          .filter(v => v !== '' || '\n')
          .map(v => v.trim())
          .join('\n');
      }
      const newSpec = survey.spec ? survey.spec.concat(question) : [question];
      await updateSurvey(newSpec);
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
