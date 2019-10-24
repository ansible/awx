import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import TemplatesListItem from './TemplateListItem';

describe('<TemplatesListItem />', () => {
  test('launch button shown to users with start capabilities', () => {
    const wrapper = mountWithContexts(
      <TemplatesListItem
        isSelected={false}
        template={{
          id: 1,
          name: 'Template 1',
          url: '/templates/job_template/1',
          type: 'job_template',
          summary_fields: {
            user_capabilities: {
              start: true,
            },
          },
        }}
      />
    );
    expect(wrapper.find('LaunchButton').exists()).toBeTruthy();
  });
  test('launch button hidden from users without start capabilities', () => {
    const wrapper = mountWithContexts(
      <TemplatesListItem
        isSelected={false}
        template={{
          id: 1,
          name: 'Template 1',
          url: '/templates/job_template/1',
          type: 'job_template',
          summary_fields: {
            user_capabilities: {
              start: false,
            },
          },
        }}
      />
    );
    expect(wrapper.find('LaunchButton').exists()).toBeFalsy();
  });
  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <TemplatesListItem
        isSelected={false}
        template={{
          id: 1,
          name: 'Template 1',
          url: '/templates/job_template/1',
          type: 'job_template',
          summary_fields: {
            user_capabilities: {
              edit: true,
            },
          },
        }}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <TemplatesListItem
        isSelected={false}
        template={{
          id: 1,
          name: 'Template 1',
          url: '/templates/job_template/1',
          type: 'job_template',
          summary_fields: {
            user_capabilities: {
              edit: false,
            },
          },
        }}
      />
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
