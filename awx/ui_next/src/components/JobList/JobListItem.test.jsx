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
  },
  created: '2019-08-08T19:24:05.344276Z',
  modified: '2019-08-08T19:24:18.162949Z',
  name: 'Demo Job Template',
  job_type: 'run',
  started: '2019-08-08T19:24:18.329589Z',
  finished: '2019-08-08T19:24:50.119995Z',
  status: 'successful',
};

describe('<JobListItem />', () => {
  let wrapper;

  beforeEach(() => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs'],
    });
    wrapper = mountWithContexts(
      <JobListItem job={mockJob} isSelected onSelect={() => {}} />,
      { context: { router: { history } } }
    );
  });

  afterEach(() => {
    wrapper.unmount();
  });

  test('initially renders successfully', () => {
    expect(wrapper.find('JobListItem').length).toBe(1);
  });

  test('launch button shown to users with launch capabilities', () => {
    expect(wrapper.find('LaunchButton').length).toBe(1);
  });

  test('launch button hidden from users without launch capabilities', () => {
    wrapper = mountWithContexts(
      <JobListItem
        job={{
          ...mockJob,
          summary_fields: { user_capabilities: { start: false } },
        }}
        detailUrl={`/jobs/playbook/${mockJob.id}`}
        onSelect={() => {}}
        isSelected={false}
      />
    );
    expect(wrapper.find('LaunchButton').length).toBe(0);
  });

  test('should hide type column when showTypeColumn is false', () => {
    expect(wrapper.find('DataListCell[aria-label="type"]').length).toBe(0);
  });

  test('should show type column when showTypeColumn is true', () => {
    wrapper = mountWithContexts(
      <JobListItem
        job={mockJob}
        showTypeColumn
        isSelected
        onSelect={() => {}}
      />
    );
    expect(wrapper.find('DataListCell[aria-label="type"]').length).toBe(1);
  });
});
