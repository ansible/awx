import React, { useState } from 'react';
import {
  Redirect,
  useHistory,
  useLocation,
  useRouteMatch,
} from 'react-router-dom';
import ContentLoading from 'components/ContentLoading';
import { CardBody } from 'components/Card';
import SurveyQuestionForm from './SurveyQuestionForm';

export default function SurveyQuestionEdit({ survey, updateSurvey }) {
  const [formError, setFormError] = useState(null);
  const history = useHistory();
  const match = useRouteMatch();
  const { search } = useLocation();
  const queryParams = new URLSearchParams(search);
  const questionVariable = decodeURIComponent(
    queryParams.get('question_variable')
  );

  if (!survey) {
    return <ContentLoading />;
  }

  const question = survey.spec.find((q) => q.variable === questionVariable);

  if (!question) {
    return (
      <Redirect
        to={`/templates/${match.params.templateType}/${match.params.id}/survey`}
      />
    );
  }

  const navigateToList = () => {
    const index = match.url.indexOf('/edit');
    history.push(match.url.substr(0, index));
  };

  const handleSubmit = async (formData) => {
    const submittedData = { ...formData };
    try {
      if (
        submittedData.variable !== question.variable &&
        survey.spec.find((q) => q.variable === submittedData.variable)
      ) {
        setFormError(
          new Error(
            `Survey already contains a question with variable named “${submittedData.variable}”`
          )
        );
        return;
      }
      const questionIndex = survey.spec.findIndex(
        (q) => q.variable === questionVariable
      );
      if (questionIndex === -1) {
        throw new Error('Question not found in spec');
      }
      if (
        submittedData.type === 'multiselect' ||
        submittedData.type === 'multiplechoice'
      ) {
        const choices = [];
        let defaultAnswers = '';
        submittedData.formattedChoices.forEach(({ choice, isDefault }, i) => {
          choices.push(choice);
          if (isDefault) {
            defaultAnswers =
              i === submittedData.formattedChoices.length - 1
                ? defaultAnswers.concat(`${choice}`)
                : defaultAnswers.concat(`${choice}\n`);
          }
        });
        submittedData.default = defaultAnswers.trim();
        submittedData.choices = choices;
      }
      delete submittedData.formattedChoices;

      await updateSurvey([
        ...survey.spec.slice(0, questionIndex),
        submittedData,
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
