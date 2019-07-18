import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import JobDetail from './JobDetail';

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
});
