import React from 'react';

import { createMemoryHistory } from 'history';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import { JobTemplatesAPI } from '../../api';
import mockJobTemplateData from './data.job_template.json';
import TemplateListItem from './TemplateListItem';

jest.mock('../../api');

describe('<TemplateListItem />', () => {
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
});
