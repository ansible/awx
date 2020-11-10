import React from 'react';
import { act } from 'react-dom/test-utils';
import { Route } from 'react-router-dom';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import TemplateSurvey from './TemplateSurvey';
import { JobTemplatesAPI, WorkflowJobTemplatesAPI } from '../../api';
import mockJobTemplateData from './shared/data.job_template.json';

jest.mock('../../api/models/JobTemplates');
jest.mock('../../api/models/WorkflowJobTemplates');

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

  test('should toggle jt survery on', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/job_template/1/survey'],
    });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <TemplateSurvey template={mockJobTemplateData} canEdit />,
        {
          context: { router: { history } },
        }
      );
    });
    wrapper.update();
    await act(() =>
      wrapper.find('Switch[aria-label="Survey Toggle"]').prop('onChange')()
    );
    wrapper.update();

    expect(JobTemplatesAPI.update).toBeCalledWith(7, { survey_enabled: false });
  });

  test('should toggle wfjt survey on', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates/workflow_job_template/1/survey'],
    });

    WorkflowJobTemplatesAPI.readSurvey.mockResolvedValueOnce({
      data: surveyData,
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <Route path="/templates/:templateType/:id/survey">
          <TemplateSurvey template={mockJobTemplateData} canEdit />
        </Route>,
        {
          context: {
            router: {
              history,
              route: {
                location: history.location,
                match: { params: { templateType: 'workflow_job_template' } },
              },
            },
          },
        }
      );
    });
    wrapper.update();
    await act(() =>
      wrapper.find('Switch[aria-label="Survey Toggle"]').prop('onChange')()
    );
    wrapper.update();
    expect(WorkflowJobTemplatesAPI.update).toBeCalledWith(7, {
      survey_enabled: false,
    });
  });
});
