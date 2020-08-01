import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import HostGroups from './HostGroups';

jest.mock('../../../api');

describe('<HostGroups />', () => {
  test('initially renders successfully', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/hosts/1/groups'],
    });
    const host = {
      id: 1,
      name: 'Foo',
      summary_fields: { inventory: { id: 1 } },
    };

    await act(async () => {
      wrapper = mountWithContexts(
        <HostGroups setBreadcrumb={() => {}} host={host} />,

        {
          context: {
            router: { history, route: { location: history.location } },
          },
        }
      );
    });
    expect(wrapper.length).toBe(1);
    expect(wrapper.find('HostGroupsList').length).toBe(1);
  });
});
