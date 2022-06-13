import React from 'react';

import { act } from 'react-dom/test-utils';
import { ProjectsAPI } from 'api';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ProjectsListItem from './ProjectListItem';

jest.mock('../../../api/models/Projects');
jest.mock('hooks/useBrandName', () => ({
  __esModule: true,
  default: () => ({
    current: 'AWX',
  }),
}));
describe('<ProjectsListItem />', () => {
  test('launch button shown to users with start capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ProjectSyncButton').exists()).toBeTruthy();
  });

  test('should render warning about missing execution environment', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
              custom_virtualenv: '/var/lib/awx/env',
              default_environment: null,
            }}
          />
        </tbody>
      </table>
    );

    expect(wrapper.find('ExclamationTrianglePopover').length).toBe(1);
  });

  test('launch button hidden from users without start capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ProjectSyncButton').exists()).toBeFalsy();
  });

  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });

  test('should call api to copy project', async () => {
    ProjectsAPI.copy.mockResolvedValue();
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );

    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(ProjectsAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    ProjectsAPI.copy.mockRejectedValue(new Error('This is an error'));

    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
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
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });
  test('should render proper revision text when project has not been synced', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ClipboardCopy').length).toBe(0);
    expect(wrapper.find('td[data-label="Revision"]').text()).toBe(
      'Sync for revision'
    );
  });
  test('should render the clipboard copy with the right text when scm revision available', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
              scm_revision: 'osofej904r09a9sf0udfsajogsdfbh4e23489adf',
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ClipboardCopy').length).toBe(1);
    expect(wrapper.find('ClipboardCopy').text()).toBe('osofej9');
  });
  test('should indicate that the revision needs to be refreshed when project sync is done', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
              scm_revision: null,
              summary_fields: {
                current_job: {
                  id: 9001,
                  status: 'successful',
                  finished: '2021-06-01T18:43:53.332201Z',
                },
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ClipboardCopy').length).toBe(0);
    expect(wrapper.find('td[data-label="Revision"]').text()).toBe(
      'Refresh for revision'
    );
    expect(wrapper.find('UndoIcon').length).toBe(1);
  });
  test('should render expected details in expanded section', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <ProjectsListItem
            rowIndex={1}
            isExpanded
            isSelected={false}
            detailUrl="/project/1"
            onSelect={() => {}}
            project={{
              id: 1,
              name: 'Project 1',
              description: 'Project 1 description',
              url: '/api/v2/projects/1',
              type: 'project',
              scm_type: 'git',
              scm_revision: '123456789',
              summary_fields: {
                organization: {
                  id: 999,
                  description: '',
                  name: 'Mock org',
                },
                last_job: {
                  id: 9000,
                  status: 'successful',
                },
                user_capabilities: {
                  start: true,
                },
                default_environment: {
                  id: 123,
                  name: 'Mock EE',
                  image: 'mock.image',
                },
              },
              custom_virtualenv: '/var/lib/awx/env',
              default_environment: 123,
              organization: 999,
            }}
          />
        </tbody>
      </table>
    );

    expect(wrapper.find('Tr').last().prop('isExpanded')).toBe(true);

    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }
    assertDetail('Description', 'Project 1 description');
    assertDetail('Organization', 'Mock org');
    assertDetail('Default Execution Environment', 'Mock EE');
    expect(wrapper.find('Detail[label="Last modified"]').length).toBe(1);
    expect(wrapper.find('Detail[label="Last used"]').length).toBe(1);
  });
});
