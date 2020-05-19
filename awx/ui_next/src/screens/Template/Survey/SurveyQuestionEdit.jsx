import React, { useState } from 'react';
import { useHistory, useRouteMatch } from 'react-router-dom';
import ContentLoading from '../../../components/ContentLoading';
import { CardBody } from '../../../components/Card';
import SurveyQuestionForm from './SurveyQuestionForm';

export default function SurveyQuestionEdit({ survey, updateSurvey }) {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const match = useRouteMatch();

  if (!survey) {
    return <ContentLoading />;
  }

  const question = survey.spec.find(q => q.variable === match.params.variable);

  const navigateToList = () => {
    const index = match.url.indexOf('/edit');
    history.push(match.url.substr(0, index));
  };

  const handleSubmit = async formData => {
    try {
      if (
        formData.variable !== question.variable &&
        survey.spec.find(q => q.variable === formData.variable)
      ) {
        setFormError(
          new Error(
            `Survey already contains a question with variable named “${formData.variable}”`
          )
        );
        return;
      }
      const questionIndex = survey.spec.findIndex(
        q => q.variable === match.params.variable
      );
      if (questionIndex === -1) {
        throw new Error('Question not found in spec');
      }
      if (formData.type === 'multiselect') {
        formData.default = formData.default
          .split('\n')
          .filter(v => v !== '' || '\n')
          .map(v => v.trim())
          .join('\n');
      }
      await updateSurvey([
        ...survey.spec.slice(0, questionIndex),
        formData,
        ...survey.spec.slice(questionIndex + 1),
      ]);
      navigateToList();
    } catch (err) {
      setFormError(err);
    }
  };

  return (
    <CardBody>
      <SurveyQuestionForm
        question={question}
        handleSubmit={handleSubmit}
        handleCancel={navigateToList}
        submitError={formError}
      />
    </CardBody>
  );
}
