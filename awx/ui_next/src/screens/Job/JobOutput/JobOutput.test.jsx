import React from 'react';

import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';

import JobOutput from './JobOutput';

async function checkOutput(wrapper, expectedLines) {
  await waitForElement(wrapper, 'div[type="job_event"]', (e) => e.length > 1);
  const jobEventLines = wrapper.find('div[type="job_event_line_text"]');
  const actualLines = [];
  jobEventLines.forEach(line => {
    actualLines.push(line.text());
  });
  expectedLines.forEach((line, index) => {
    expect(actualLines[index]).toEqual(line);
  });
}

describe('<JobOutput />', () => {
  const mockDetails = {
    name: 'Foo',
  };

  test('initially renders succesfully', async done => {
    const wrapper = mountWithContexts(<JobOutput job={mockDetails} />);
    // wait until not loading
    await waitForElement(wrapper, 'EmptyStateBody', (e) => e.length === 0);

    // await checkOutput(wrapper, [
    //   '',
    //   'PLAY [localhost] ***************************************************************08:00:52',
    //   '',
    //   'TASK [Gathering Facts] *********************************************************08:00:52',
    //   'ok: [localhost]',
    //   '',
    //   'TASK [Check Slack accounts against ldap] ***************************************08:00:53',
    //   'changed: [localhost]',
    //   '',
    //   'TASK [E-mail output] ***********************************************************08:00:58',
    //   'skipping: [localhost]',
    //   '',
    //   'PLAY RECAP *********************************************************************08:00:58',
    //   'localhost                  : ok=2    changed=1    unreachable=0    failed=0    skipped=1    rescued=0    ignored=0   ',
    //   '',
    // ]);
    done();
  });
});
