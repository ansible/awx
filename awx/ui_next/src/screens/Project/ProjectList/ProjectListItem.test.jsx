import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import ProjectsListItem from './ProjectListItem';

describe('<ProjectsListItem />', () => {
  test('launch button shown to users with start capabilities', () => {
    const wrapper = mountWithContexts(
      <ProjectsListItem
        isSelected={false}
        detailUrl="/project/1"
        onSelect={() => {}}
        project={{
          id: 1,
          name: 'Project 1',
          url: '/api/v2/projects/1',
          type: 'project',
          scm_type: 'git',
          scm_revision: '7788f7erga0jijodfgsjisiodf98sdga9hg9a98gaf',
          summary_fields: {
            last_job: {
              id: 9000,
              status: 'successful',
            },
            user_capabilities: {
              start: true,
            },
          },
        }}
      />
    );
    expect(wrapper.find('ProjectSyncButton').exists()).toBeTruthy();
  });
  test('launch button hidden from users without start capabilities', () => {
    const wrapper = mountWithContexts(
      <ProjectsListItem
        isSelected={false}
        detailUrl="/project/1"
        onSelect={() => {}}
        project={{
          id: 1,
          name: 'Project 1',
          url: '/api/v2/projects/1',
          type: 'project',
          scm_type: 'git',
          scm_revision: '7788f7erga0jijodfgsjisiodf98sdga9hg9a98gaf',
          summary_fields: {
            last_job: {
              id: 9000,
              status: 'successful',
            },
            user_capabilities: {
              start: false,
            },
          },
        }}
      />
    );
    expect(wrapper.find('ProjectSyncButton').exists()).toBeFalsy();
  });
  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <ProjectsListItem
        isSelected={false}
        detailUrl="/project/1"
        onSelect={() => {}}
        project={{
          id: 1,
          name: 'Project 1',
          url: '/api/v2/projects/1',
          type: 'project',
          scm_type: 'git',
          scm_revision: '7788f7erga0jijodfgsjisiodf98sdga9hg9a98gaf',
          summary_fields: {
            last_job: {
              id: 9000,
              status: 'successful',
            },
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
      <ProjectsListItem
        isSelected={false}
        detailUrl="/project/1"
        onSelect={() => {}}
        project={{
          id: 1,
          name: 'Project 1',
          url: '/api/v2/projects/1',
          type: 'project',
          scm_type: 'git',
          scm_revision: '7788f7erga0jijodfgsjisiodf98sdga9hg9a98gaf',
          summary_fields: {
            last_job: {
              id: 9000,
              status: 'successful',
            },
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
