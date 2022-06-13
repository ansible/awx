import React from 'react';
import { Switch, Route } from 'react-router-dom';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import SurveyQuestionEdit from './SurveyQuestionEdit';

const survey = {
  spec: [
    {
      question_name: 'What is the foo?',
      question_description: 'more about the foo',
      variable: 'foo',
      required: true,
      type: 'text',
      min: 0,
      max: 1024,
    },
    {
      question_name: 'Who shot the sheriff?',
      question_description: 'they did not shoot the deputy',
      variable: 'bar',
      required: true,
      type: 'textarea',
      min: 0,
      max: 1024,
    },
  ],
};

describe('<SurveyQuestionEdit />', () => {
  let updateSurvey;
  let history;
  let wrapper;

  describe('with question_variable present', () => {
    beforeEach(() => {
      history = createMemoryHistory({
        initialEntries: [
          '/templates/job_templates/1/survey/edit?question_variable=foo',
        ],
      });
      updateSurvey = jest.fn();
      wrapper = mountWithContexts(
        <Switch>
          <Route path="/templates/:templateType/:id/survey/edit">
            <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
          </Route>
        </Switch>,
        {
          context: { router: { history } },
        }
      );
    });

    test('should render form', () => {
      expect(wrapper.find('SurveyQuestionForm')).toHaveLength(1);
    });

    test('should call updateSurvey', () => {
      act(() => {
        wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
          question_name: 'new question',
          variable: 'question',
          type: 'text',
        });
      });
      wrapper.update();

      expect(updateSurvey).toHaveBeenCalledWith([
        {
          question_name: 'new question',
          variable: 'question',
          type: 'text',
        },
        survey.spec[1],
      ]);
    });

    test('should set formError', async () => {
      const realConsoleError = global.console.error;
      global.console.error = jest.fn();
      const err = new Error('oops');
      updateSurvey.mockImplementation(() => {
        throw err;
      });

      act(() => {
        wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
          question_name: 'new question',
          variable: 'question',
          type: 'text',
        });
      });
      wrapper.update();

      expect(wrapper.find('SurveyQuestionForm').prop('submitError')).toEqual(
        err
      );
      global.console.error = realConsoleError;
    });

    test('should generate error for duplicate variable names', async () => {
      const realConsoleError = global.console.error;
      global.console.error = jest.fn();

      act(() => {
        wrapper.find('SurveyQuestionForm').invoke('handleSubmit')({
          question_name: 'new question',
          variable: 'bar',
          type: 'text',
        });
      });
      wrapper.update();

      const err = wrapper.find('SurveyQuestionForm').prop('submitError');
      expect(err.message).toEqual(
        'Survey already contains a question with variable named “bar”'
      );
      global.console.error = realConsoleError;
    });
  });

  describe('without question_variable present', () => {
    test('should redirect back to the survey list', () => {
      history = createMemoryHistory({
        initialEntries: ['/templates/job_templates/1/survey/edit'],
      });
      updateSurvey = jest.fn();
      act(() => {
        wrapper = mountWithContexts(
          <Switch>
            <Route path="/templates/:templateType/:id/survey/edit">
              <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
            </Route>
          </Switch>,
          {
            context: { router: { history } },
          }
        );
      });

      expect(history.location.pathname).toEqual(
        '/templates/job_templates/1/survey'
      );
    });
  });

  test('should handle multiplechoice as array', () => {
    const survey = {
      spec: [
        {
          question_name: 'What is the foo?',
          question_description: 'more about the foo',
          variable: 'foo',
          required: true,
          type: 'multiplechoice',
          choices: ['one', 'two', 'three'],
          default: '',
          min: 0,
          max: 1024,
        },
      ],
    };
    history = createMemoryHistory({
      initialEntries: [
        '/templates/job_templates/1/survey/edit?question_variable=foo',
      ],
    });
    updateSurvey = jest.fn();
    wrapper = mountWithContexts(
      <Switch>
        <Route path="/templates/:templateType/:id/survey/edit">
          <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
        </Route>
      </Switch>,
      {
        context: { router: { history } },
      }
    );

    const inputs = wrapper.find('MultipleChoiceField TextInput');
    expect(inputs).toHaveLength(3);
    expect(inputs.at(0).prop('value')).toEqual('one');
    expect(inputs.at(1).prop('value')).toEqual('two');
    expect(inputs.at(2).prop('value')).toEqual('three');
  });

  test('should handle multiplechoice as string', () => {
    const survey = {
      spec: [
        {
          question_name: 'What is the foo?',
          question_description: 'more about the foo',
          variable: 'foo',
          required: true,
          type: 'multiplechoice',
          choices: 'one\ntwo\nthree',
          default: '',
          min: 0,
          max: 1024,
        },
      ],
    };
    history = createMemoryHistory({
      initialEntries: [
        '/templates/job_templates/1/survey/edit?question_variable=foo',
      ],
    });
    updateSurvey = jest.fn();
    wrapper = mountWithContexts(
      <Switch>
        <Route path="/templates/:templateType/:id/survey/edit">
          <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
        </Route>
      </Switch>,
      {
        context: { router: { history } },
      }
    );

    const inputs = wrapper.find('MultipleChoiceField TextInput');
    expect(inputs).toHaveLength(3);
    expect(inputs.at(0).prop('value')).toEqual('one');
    expect(inputs.at(1).prop('value')).toEqual('two');
    expect(inputs.at(2).prop('value')).toEqual('three');
  });

  test('should handle multiselect as array', () => {
    const survey = {
      spec: [
        {
          question_name: 'What is the foo?',
          question_description: 'more about the foo',
          variable: 'foo',
          required: true,
          type: 'multiselect',
          choices: ['one', 'two', 'three'],
          default: '',
          min: 0,
          max: 1024,
        },
      ],
    };
    history = createMemoryHistory({
      initialEntries: [
        '/templates/job_templates/1/survey/edit?question_variable=foo',
      ],
    });
    updateSurvey = jest.fn();
    wrapper = mountWithContexts(
      <Switch>
        <Route path="/templates/:templateType/:id/survey/edit">
          <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
        </Route>
      </Switch>,
      {
        context: { router: { history } },
      }
    );

    const inputs = wrapper.find('MultipleChoiceField TextInput');
    expect(inputs).toHaveLength(3);
    expect(inputs.at(0).prop('value')).toEqual('one');
    expect(inputs.at(1).prop('value')).toEqual('two');
    expect(inputs.at(2).prop('value')).toEqual('three');
  });

  test('should handle multiselect as string', () => {
    const survey = {
      spec: [
        {
          question_name: 'What is the foo?',
          question_description: 'more about the foo',
          variable: 'foo',
          required: true,
          type: 'multiselect',
          choices: 'one\ntwo\nthree',
          default: '',
          min: 0,
          max: 1024,
        },
      ],
    };
    history = createMemoryHistory({
      initialEntries: [
        '/templates/job_templates/1/survey/edit?question_variable=foo',
      ],
    });
    updateSurvey = jest.fn();
    wrapper = mountWithContexts(
      <Switch>
        <Route path="/templates/:templateType/:id/survey/edit">
          <SurveyQuestionEdit survey={survey} updateSurvey={updateSurvey} />
        </Route>
      </Switch>,
      {
        context: { router: { history } },
      }
    );

    const inputs = wrapper.find('MultipleChoiceField TextInput');
    expect(inputs).toHaveLength(3);
    expect(inputs.at(0).prop('value')).toEqual('one');
    expect(inputs.at(1).prop('value')).toEqual('two');
    expect(inputs.at(2).prop('value')).toEqual('three');
  });
});
