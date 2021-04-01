import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import ExecutionEnvironmentTemplateListItem from './ExecutionEnvironmentTemplateListItem';

describe('<ExecutionEnvironmentTemplateListItem/>', () => {
  let wrapper;
  const template = {
    id: 1,
    name: 'Foo',
    type: 'job_template',
  };

  test('should mount successfully', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentTemplateListItem
          template={template}
          detailUrl={`/templates/${template.type}/${template.id}/details`}
        />
      );
    });
    expect(wrapper.find('ExecutionEnvironmentTemplateListItem').length).toBe(1);
    expect(wrapper.find('DataListCell[aria-label="Name"]').text()).toBe(
      template.name
    );
    expect(
      wrapper.find('DataListCell[aria-label="Template type"]').text()
    ).toBe('Job Template');
  });

  test('should distinguish template types', async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <ExecutionEnvironmentTemplateListItem
          template={{ ...template, type: 'workflow_job_template' }}
          detailUrl={`/templates/${template.type}/${template.id}/details`}
        />
      );
    });
    expect(wrapper.find('ExecutionEnvironmentTemplateListItem').length).toBe(1);
    expect(
      wrapper.find('DataListCell[aria-label="Template type"]').text()
    ).toBe('Workflow Job Template');
  });
});
