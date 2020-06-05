import React from 'react';

import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ProjectsListItem from './ProjectListItem';
import { ProjectsAPI } from '../../../api';

jest.mock('../../../api/models/Projects');

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

  test('should call api to copy project', async () => {
    ProjectsAPI.copy.mockResolvedValue();
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
              copy: true,
            },
          },
        }}
      />
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(ProjectsAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    ProjectsAPI.copy.mockRejectedValue(new Error());

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
              copy: true,
            },
          },
        }}
      />
    );
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    wrapper.update();
    expect(wrapper.find('Modal').prop('isOpen')).toBe(true);
    jest.clearAllMocks();
  });
  test('should not render copy button', async () => {
    const wrapper = mountWithContexts(
      <ProjectsListItem
        isSelected={false}
        detailUrl="/foo/bar"
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
              copy: false,
            },
          },
        }}
      />
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
  test('should render disabled copy to clipboard button', () => {
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
          scm_revision: '',
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
    expect(
      wrapper.find('span[aria-label="copy to clipboard disabled"]').text()
    ).toBe('Sync for revision');
    expect(wrapper.find('ClipboardCopyButton').prop('isDisabled')).toBe(true);
  });
});
