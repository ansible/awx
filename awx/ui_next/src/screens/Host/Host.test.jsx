import React from 'react';
import { createMemoryHistory } from 'history';
import { HostsAPI } from '@api';
import { mountWithContexts, waitForElement } from '@testUtils/enzymeHelpers';
import mockDetails from './data.host.json';
import Host from './Host';

jest.mock('@api');

const mockMe = {
  is_super_user: true,
  is_system_auditor: false,
};

describe('<Host />', () => {
  test('initially renders succesfully', () => {
    HostsAPI.readDetail.mockResolvedValue({ data: mockDetails });
    mountWithContexts(<Host setBreadcrumb={() => {}} me={mockMe} />);
  });

  test('should show content error when user attempts to navigate to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/hosts/1/foobar'],
    });
    const wrapper = mountWithContexts(
      <Host setBreadcrumb={() => {}} me={mockMe} />,
      {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match: {
                params: { id: 1 },
                url: '/hosts/1/foobar',
                path: '/host/1/foobar',
              },
            },
          },
        },
      }
    );
    await waitForElement(wrapper, 'ContentError', el => el.length === 1);
  });
});
