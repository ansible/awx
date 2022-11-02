import React from 'react';

import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { JobTemplatesAPI } from 'api';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import mockJobTemplateData from './data.job_template.json';
import TemplateListItem from './TemplateListItem';

jest.mock('../../api');

describe('<TemplateListItem />', () => {
  test('should display expected data', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            template={{
              id: 1,
              name: 'Template 1',
              url: '/templates/job_template/1',
              type: 'job_template',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Foo',
                },
                user_capabilities: {
                  start: true,
                },
                recent_jobs: [
                  {
                    id: 123,
                    name: 'Template 1',
                    status: 'failed',
                    finished: '2020-02-26T22:38:41.037991Z',
                  },
                ],
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Td[dataLabel="Name"]').text()).toBe('Template 1');
    expect(wrapper.find('Td[dataLabel="Type"]').text()).toBe('Job Template');
    expect(wrapper.find('Td[dataLabel="Organization"]').text()).toBe('Foo');
    expect(
      wrapper.find('Td[dataLabel="Organization"]').find('Link').prop('to')
    ).toBe('/organizations/1/details');
    expect(wrapper.find('Td[dataLabel="Last Ran"]').text()).toBe(
      '2/26/2020, 10:38:41 PM'
    );
  });

  test('launch button shown to users with start capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
        </tbody>
      </table>
    );
    expect(wrapper.find('LaunchButton').exists()).toBeTruthy();
  });
  test('launch button hidden from users without start capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
        </tbody>
      </table>
    );
    expect(wrapper.find('LaunchButton').exists()).toBeFalsy();
  });
  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
        </tbody>
      </table>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
  test('missing resource icon is shown.', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
        </tbody>
      </table>
    );
    expect(wrapper.find('ExclamationTriangleIcon').exists()).toBe(true);
  });
  test('missing resource icon is not shown when there is a project and an inventory.', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
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
                project: { name: 'Foo', id: 2 },
                inventory: { name: 'Bar', id: 2 },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ExclamationTriangleIcon').exists()).toBe(false);
  });
  test('missing resource icon is not shown when inventory is prompt_on_launch, and a project', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            template={{
              id: 1,
              name: 'Template 1',
              url: '/templates/job_template/1',
              type: 'job_template',
              ask_inventory_on_launch: true,
              summary_fields: {
                user_capabilities: {
                  edit: false,
                },
                project: { name: 'Foo', id: 2 },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ExclamationTriangleIcon').exists()).toBe(false);
  });
  test('missing resource icon is not shown type is workflow_job_template', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            template={{
              id: 1,
              name: 'Template 1',
              url: '/templates/job_template/1',
              type: 'workflow_job_template',
              summary_fields: {
                user_capabilities: {
                  edit: false,
                },
              },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ExclamationTriangleIcon').exists()).toBe(false);
  });
  test('clicking on template from templates list navigates properly', () => {
    const history = createMemoryHistory({
      initialEntries: ['/templates'],
    });
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={{
              id: 1,
              name: 'Template 1',
              summary_fields: {
                user_capabilities: {
                  edit: false,
                },
              },
            }}
          />
        </tbody>
      </table>,
      { context: { router: { history } } }
    );
    wrapper.find('Link').simulate('click', { button: 0 });
    expect(history.location.pathname).toEqual(
      '/templates/job_template/1/details'
    );
  });
  test('should call api to copy template', async () => {
    JobTemplatesAPI.copy.mockResolvedValue();

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={mockJobTemplateData}
          />
        </tbody>
      </table>
    );
    await act(async () =>
      wrapper.find('Button[aria-label="Copy"]').prop('onClick')()
    );
    expect(JobTemplatesAPI.copy).toHaveBeenCalled();
    jest.clearAllMocks();
  });

  test('should render proper alert modal on copy error', async () => {
    JobTemplatesAPI.copy.mockRejectedValue(new Error());

    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={mockJobTemplateData}
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
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={{
              ...mockJobTemplateData,
              summary_fields: { user_capabilities: { copy: false } },
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('CopyButton').length).toBe(0);
  });

  test('should render visualizer button for workflow', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={{
              ...mockJobTemplateData,
              type: 'workflow_job_template',
            }}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ProjectDiagramIcon').length).toBe(1);
  });

  test('should not render visualizer button for job template', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            detailUrl="/templates/job_template/1/details"
            template={mockJobTemplateData}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ProjectDiagramIcon').length).toBe(0);
  });

  test('should render warning about missing execution environment', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            template={{
              id: 1,
              name: 'Template 1',
              url: '/templates/job_template/1',
              type: 'job_template',
              summary_fields: {
                inventory: {
                  id: 1,
                  name: 'Demo Inventory',
                  description: '',
                  has_active_failures: false,
                  total_hosts: 0,
                  hosts_with_active_failures: 0,
                  total_groups: 0,
                  has_inventory_sources: false,
                  total_inventory_sources: 0,
                  inventory_sources_with_failures: 0,
                  organization_id: 1,
                  kind: '',
                },
                project: {
                  id: 6,
                  name: 'Demo Project',
                  description: '',
                  status: 'never updated',
                  scm_type: 'git',
                },
                user_capabilities: {
                  edit: true,
                  delete: true,
                  start: true,
                  schedule: true,
                  copy: true,
                },
              },
              custom_virtualenv: '/var/lib/awx/env',
              execution_environment: null,
              project: 6,
              inventory: 1,
            }}
          />
        </tbody>
      </table>
    );

    expect(wrapper.find('ExclamationTriangleIconWarning').length).toBe(1);
  });

  test('should render expected details in expanded section', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            isSelected={false}
            isExpanded
            detailUrl="/templates/job_template/1/details"
            template={{
              ...mockJobTemplateData,
              description: 'mock description',
            }}
          />
        </tbody>
      </table>
    );

    wrapper.update();
    expect(wrapper.find('Tr').last().prop('isExpanded')).toBe(true);

    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    assertDetail('Description', 'mock description');
    assertDetail('Inventory', "Mike's Inventory");
    assertDetail('Project', "Mike's Project");
    assertDetail('Execution Environment', 'Mock EE 1.2.3');
    expect(
      wrapper.find('Detail[label="Credentials"]').containsAllMatchingElements([
        <span>
          <strong>SSH:</strong>Credential 1
        </span>,
        <span>
          <strong>Awx:</strong>Credential 2
        </span>,
      ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Labels"]')
        .containsAllMatchingElements([<span>L_91o2</span>])
    ).toEqual(true);
    expect(wrapper.find(`Detail[label="Activity"] Sparkline`)).toHaveLength(1);
  });

  test('should not load Activity', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            template={{
              ...mockJobTemplateData,
              summary_fields: {
                user_capabilities: {},
                recent_jobs: [],
              },
            }}
          />
        </tbody>
      </table>
    );
    const activity_detail = wrapper.find(`Detail[label="Activity"]`).at(0);
    expect(activity_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load Credentials', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            template={{
              ...mockJobTemplateData,
              summary_fields: {
                user_capabilities: {},
                credentials: [],
              },
            }}
          />
        </tbody>
      </table>
    );
    const credentials_detail = wrapper
      .find(`Detail[label="Credentials"]`)
      .at(0);
    expect(credentials_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load Labels', async () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <TemplateListItem
            template={{
              ...mockJobTemplateData,
              summary_fields: {
                user_capabilities: {},
                labels: {
                  results: [],
                },
              },
            }}
          />
        </tbody>
      </table>
    );
    const labels_detail = wrapper.find(`Detail[label="Labels"]`).at(0);
    expect(labels_detail.prop('isEmpty')).toEqual(true);
  });
});
