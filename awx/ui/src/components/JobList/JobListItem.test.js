import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import JobListItem from './JobListItem';

const mockJob = {
  id: 123,
  type: 'job',
  url: '/api/v2/jobs/123/',
  summary_fields: {
    user_capabilities: {
      delete: true,
      start: true,
    },
    schedule: {
      name: 'mock schedule',
      id: 999,
    },
    unified_job_template: {
      unified_job_type: 'job',
      id: 1,
    },
  },
  created: '2019-08-08T19:24:05.344276Z',
  modified: '2019-08-08T19:24:18.162949Z',
  name: 'Demo Job Template',
  job_type: 'run',
  launch_type: 'scheduled',
  started: '2019-08-08T19:24:18.329589Z',
  finished: '2019-08-08T19:24:50.119995Z',
  status: 'successful',
  job_slice_number: 1,
  job_slice_count: 3,
  execution_environment: 1,
};

describe('<JobListItem />', () => {
  let wrapper;

  beforeEach(() => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs'],
    });
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem job={mockJob} isSelected onSelect={() => {}} />
        </tbody>
      </table>,
      { context: { router: { history } } }
    );
  });

  function assertDetail(label, value) {
    expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
    expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
  }

  test('initially renders successfully', () => {
    expect(wrapper.find('JobListItem').length).toBe(1);
  });

  test('should display expected details', () => {
    assertDetail('Job Slice', '1/3');
    assertDetail('Schedule', 'mock schedule');
  });

  test('launch button shown to users with launch capabilities', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
  });

  test('launch button shown to users with launch capabilities', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
  });

  test('should render source data in expanded view', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            isExpanded
            inventorySourceLabels={[
              ['scm', 'Sourced from Project'],
              ['file', 'File, Directory or Script'],
            ]}
            job={{
              ...mockJob,
              type: 'inventory_update',
              source: 'scm',
              summary_fields: { user_capabilities: { start: false } },
            }}
            detailUrl={`/jobs/playbook/${mockJob.id}`}
            onSelect={() => {}}
            isSelected={false}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('ExpandableRowContent')).toHaveLength(1);
    expect(
      wrapper.find('dd[data-cy="job-inventory-source-type-value"]').text()
    ).toBe('Sourced from Project');
  });
  test('launch button hidden from users without launch capabilities', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              summary_fields: { user_capabilities: { start: false } },
            }}
            detailUrl={`/jobs/playbook/${mockJob.id}`}
            onSelect={() => {}}
            isSelected={false}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('LaunchButton').length).toBe(0);
  });

  test('should hide type column when showTypeColumn is false', () => {
    expect(wrapper.find('Td[dataLabel="Type"]').length).toBe(0);
  });

  test('should show type column when showTypeColumn is true', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={mockJob}
            showTypeColumn
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Td[dataLabel="Type"]').length).toBe(1);
  });

  test('should not show schedule detail in expanded view', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              summary_fields: {},
            }}
            showTypeColumn
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Detail[label="Schedule"] dt').length).toBe(1);
  });

  test('should not display EE for canceled jobs', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              status: 'canceled',
              execution_environment: null,
            }}
            showTypeColumn
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Detail[label="Execution Environment"]').length).toBe(
      0
    );
  });

  test('should display missing resource for completed jobs and missing EE', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={mockJob}
            showTypeColumn
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('Detail[label="Execution Environment"]').length).toBe(
      1
    );
    expect(
      wrapper.find('Detail[label="Execution Environment"] dd').text()
    ).toBe('Missing resource');
  });

  test('should not load Source', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            inventorySourceLabels={[]}
            job={{
              ...mockJob,
              type: 'inventory_update',
              summary_fields: {
                user_capabilities: {},
              },
            }}
          />
        </tbody>
      </table>
    );
    const source_detail = wrapper.find(`Detail[label="Source"]`).at(0);
    expect(source_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load Credentials', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              type: 'inventory_update',
              summary_fields: {
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
});

describe('<JobListItem with failed job />', () => {
  let wrapper;

  beforeEach(() => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs'],
    });
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{ ...mockJob, status: 'failed' }}
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>,
      { context: { router: { history } } }
    );
  });

  test('launch button shown to users with launch capabilities', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
  });

  test('dropdown should be displayed in case of failed job', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
    const dropdown = wrapper.find('Dropdown');
    expect(dropdown).toHaveLength(1);
    expect(dropdown.find('DropdownItem')).toHaveLength(0);
    dropdown.find('button').simulate('click');
    wrapper.update();
    expect(wrapper.find('DropdownItem')).toHaveLength(3);
  });

  test('dropdown should not be rendered for job type different of playbook run', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              status: 'failed',
              type: 'project_update',
            }}
            onSelect={() => {}}
            isSelected
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('LaunchButton').length).toBe(1);
    expect(wrapper.find('Dropdown')).toHaveLength(0);
  });

  test('launch button hidden from users without launch capabilities', () => {
    wrapper = mountWithContexts(
      <table>
        <tbody>
          <JobListItem
            job={{
              ...mockJob,
              status: 'failed',
              summary_fields: { user_capabilities: { start: false } },
            }}
            detailUrl={`/jobs/playbook/${mockJob.id}`}
            onSelect={() => {}}
            isSelected={false}
          />
        </tbody>
      </table>
    );
    expect(wrapper.find('LaunchButton').length).toBe(0);
  });
});
