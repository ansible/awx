import React from 'react';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../enzymeHelpers';
import { sleep } from '../../../../testUtils';
import Organization from '../../../../../src/pages/Organizations/screens/Organization/Organization';
import { OrganizationsAPI } from '../../../../../src/api';

jest.mock('../../../../../src/api');

describe.only('<Organization />', () => {
  const me = {
    is_super_user: true,
    is_system_auditor: false
  };

  test('initially renders succesfully', () => {
    mountWithContexts(<Organization me={me} />);
  });

  test('notifications tab shown/hidden based on permissions', async () => {
    OrganizationsAPI.readDetail.mockResolvedValue({
      data: {
        id: 1,
        name: 'foo'
      }
    });
    OrganizationsAPI.read.mockResolvedValue({
      data: {
        results: []
      }
    });
    const history = createMemoryHistory({
      initialEntries: ['/organizations/1/details'],
    });
    const match = { path: '/organizations/:id', url: '/organizations/1' };
    const wrapper = mountWithContexts(
      <Organization
        me={me}
        setBreadcrumb={() => {}}
      />,
      {
        context: {
          router: {
            history,
            route: {
              location: history.location,
              match
            }
          }
        }
      }
    );
    await sleep(0);
    wrapper.update();
    expect(wrapper.find('.pf-c-tabs__item').length).toBe(3);
    expect(wrapper.find('.pf-c-tabs__button[children="Notifications"]').length).toBe(0);
    wrapper.find('Organization').setState({
      isNotifAdmin: true
    });
    expect(wrapper.find('.pf-c-tabs__item').length).toBe(4);
    expect(wrapper.find('button.pf-c-tabs__button[children="Notifications"]').length).toBe(1);
  });
});
