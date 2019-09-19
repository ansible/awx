import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import { sleep } from '@testUtils/testUtils';
import JobDetail from './JobDetail';
import { JobsAPI, ProjectUpdatesAPI } from '@api';

jest.mock('@api');

describe('<JobDetail />', () => {
  let job;

  beforeEach(() => {
    job = {
      name: 'Foo',
      summary_fields: {},
    };
  });

  test('initially renders succesfully', () => {
    mountWithContexts(<JobDetail job={job} />);
  });

  test('should display a Close button', () => {
    const wrapper = mountWithContexts(<JobDetail job={job} />);

    expect(wrapper.find('Button[aria-label="close"]').length).toBe(1);
    wrapper.unmount();
  });

  test('should display details', () => {
    job.status = 'Successful';
    job.started = '2019-07-02T17:35:22.753817Z';
    job.finished = '2019-07-02T17:35:34.910800Z';

    const wrapper = mountWithContexts(<JobDetail job={job} />);
    const details = wrapper.find('Detail');

    function assertDetail(detail, label, value) {
      expect(detail.prop('label')).toEqual(label);
      expect(detail.prop('value')).toEqual(value);
    }

    assertDetail(details.at(0), 'Status', 'Successful');
    assertDetail(details.at(1), 'Started', job.started);
    assertDetail(details.at(2), 'Finished', job.finished);
  });

  test('should display credentials', () => {
    job.summary_fields.credentials = [
      {
        id: 1,
        name: 'Foo',
        cloud: false,
        kind: 'ssh',
      },
    ];
    const wrapper = mountWithContexts(<JobDetail job={job} />);
    const credentialChip = wrapper.find('CredentialChip');

    expect(credentialChip.prop('credential')).toEqual(
      job.summary_fields.credentials[0]
    );
  });
  test('should properly delete job', () => {
    job = {
      name: 'Rage',
      id: 1,
      type: 'job',
      summary_fields: {
        job_template: { name: 'Spud' },
      },
    };
    const wrapper = mountWithContexts(<JobDetail job={job} />);
    wrapper
      .find('button')
      .at(0)
      .invoke('onClick')();
    const modal = wrapper.find('Modal');
    expect(modal.length).toBe(1);
    modal.find('button[aria-label="delete"]').invoke('onClick')();
    expect(JobsAPI.destroy).toHaveBeenCalledTimes(1);
  });

  test('should display error modal when a job does not delete properly', async () => {
    job = {
      name: 'Angry',
      id: 'a',
      type: 'project_updates',
      summary_fields: {
        job_template: { name: 'Peanut' },
      },
    };
    const wrapper = mountWithContexts(<JobDetail job={job} />);
    wrapper
      .find('button')
      .at(0)
      .invoke('onClick')();
    const modal = wrapper.find('Modal');
    ProjectUpdatesAPI.destroy.mockRejectedValue(
      new Error({
        response: {
          config: {
            method: 'delete',
            url: '/api/v2/project_updates/1',
          },
          data: 'An error occurred',
          status: 404,
        },
      })
    );
    modal.find('button[aria-label="delete"]').invoke('onClick')();
    await sleep(1);
    wrapper.update();
    const errorModal = wrapper.find('ErrorDetail__Expandable');
    expect(errorModal.length).toBe(1);
  });
});
