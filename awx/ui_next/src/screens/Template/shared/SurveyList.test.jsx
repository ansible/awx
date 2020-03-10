import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import SurveyList from './SurveyList';
import { JobTemplatesAPI } from '@api';
import mockJobTemplateData from './data.job_template.json';

jest.mock('@api/models/JobTemplates');

describe('<SurveyList />', () => {
  beforeEach(() => {
    JobTemplatesAPI.readSurvey.mockResolvedValue({
      data: {
        name: 'Survey',
        description: 'description for survey',
        spec: [{ question_name: 'Foo', type: 'text', default: 'Bar' }],
      },
    });
  });
  test('expect component to mount successfully', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(wrapper.length).toBe(1);
  });
  test('expect api to be called to get survey', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(JobTemplatesAPI.readSurvey).toBeCalledWith(7);

    wrapper.update();
    expect(wrapper.find('SurveyListItem').length).toBe(1);
  });
  test('error in retrieving the survey throws an error', async () => {
    JobTemplatesAPI.readSurvey.mockRejectedValue(new Error());
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList template={{ ...mockJobTemplateData, id: 'a' }} />
      );
    });

    wrapper.update();

    expect(wrapper.find('ContentError').length).toBe(1);
  });
  test('can toggle survey on and off', async () => {
    JobTemplatesAPI.update.mockResolvedValue();
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList
          template={{ ...mockJobTemplateData, survey_enabled: false }}
        />
      );
    });

    expect(wrapper.find('Switch').length).toBe(1);
    expect(wrapper.find('Switch').prop('isChecked')).toBe(false);
    await act(async () => {
      wrapper.find('Switch').invoke('onChange')(true);
    });

    wrapper.update();

    expect(wrapper.find('Switch').prop('isChecked')).toBe(true);
    expect(JobTemplatesAPI.update).toBeCalledWith(7, {
      survey_enabled: true,
    });
  });

  test('selectAll enables delete button and calls the api to delete properly', async () => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList
          template={{ ...mockJobTemplateData, survey_enabled: false }}
        />
      );
    });
    await waitForElement(wrapper, 'SurveyListItem');
    expect(wrapper.find('Button[variant="danger"]').prop('isDisabled')).toBe(
      true
    );

    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(false);
    act(() => {
      wrapper.find('Checkbox[aria-label="Select all"]').invoke('onChange')(
        { target: { checked: true } },
        true
      );
    });

    wrapper.update();

    expect(
      wrapper.find('Checkbox[aria-label="Select all"]').prop('isChecked')
    ).toBe(true);

    expect(wrapper.find('Button[variant="danger"]').prop('isDisabled')).toBe(
      false
    );
    act(() => {
      wrapper.find('Button[variant="danger"]').invoke('onClick')();
    });

    wrapper.update();

    await act(() =>
      wrapper.find('Button[aria-label="confirm delete"]').invoke('onClick')()
    );
    expect(JobTemplatesAPI.destroySurvey).toBeCalledWith(7);
  });
});
describe('Survey with no questions', () => {
  test('Survey with no questions renders empty state', async () => {
    JobTemplatesAPI.readSurvey.mockResolvedValue({});
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <SurveyList template={mockJobTemplateData} />
      );
    });
    expect(wrapper.find('ContentEmpty').length).toBe(1);
    expect(wrapper.find('SurveyListItem').length).toBe(0);
  });
});
