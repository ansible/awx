import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import TemplateSurvey from './TemplateSurvey';
import { JobTemplatesAPI } from '@api';
import mockJobTemplateData from './shared/data.job_template.json';

jest.mock('@api/models/JobTemplates');

const surveyData = {
  name: 'Survey',
  description: 'description for survey',
  spec: [
    { question_name: 'Foo', type: 'text', default: 'Bar', variable: 'foo' },
  ],
};

describe('<TemplateSurvey />', () => {
  beforeEach(() => {
    JobTemplatesAPI.readSurvey.mockResolvedValue({
      data: surveyData,
    });
  });

  test('should fetch survey from API', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/survey'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <TemplateSurvey template={mockJobTemplateData} />,
        {
          context: { router: { history } },
        }
      );
    });
    wrapper.update();
    expect(JobTemplatesAPI.readSurvey).toBeCalledWith(7);

    expect(wrapper.find('SurveyList').prop('survey')).toEqual(surveyData);
  });

  test('should display error in retrieving survey', async () => {
    JobTemplatesAPI.readSurvey.mockRejectedValue(new Error());
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <TemplateSurvey template={{ ...mockJobTemplateData, id: 'a' }} />
      );
    });

    wrapper.update();

    expect(wrapper.find('ContentError').length).toBe(1);
  });

  test('should update API with survey changes', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/survey'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <TemplateSurvey template={mockJobTemplateData} />,
        {
          context: { router: { history } },
        }
      );
    });
    wrapper.update();

    await act(async () => {
      await wrapper.find('SurveyList').invoke('updateSurvey')([
        { question_name: 'Foo', type: 'text', default: 'One', variable: 'foo' },
        { question_name: 'Bar', type: 'text', default: 'Two', variable: 'bar' },
      ]);
    });
    expect(JobTemplatesAPI.updateSurvey).toHaveBeenCalledWith(7, {
      name: 'Survey',
      description: 'description for survey',
      spec: [
        { question_name: 'Foo', type: 'text', default: 'One', variable: 'foo' },
        { question_name: 'Bar', type: 'text', default: 'Two', variable: 'bar' },
      ],
    });
  });
});
