import React from 'react';
import { createMemoryHistory } from 'history';
import { shallow } from 'enzyme';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Hosts from './Hosts';

jest.mock('../../api');

describe('<Hosts />', () => {
  test('should display a breadcrumb heading', () => {
    const wrapper = shallow(<Hosts />);

    const header = wrapper.find('ScreenHeader');
    expect(header.prop('streamType')).toEqual('host');
    expect(header.prop('breadcrumbConfig')).toEqual({
      '/hosts': 'Hosts',
      '/hosts/add': 'Create New Host',
    });
  });

  test('should render Host component', async () => {
    let wrapper;
    const history = createMemoryHistory({
      initialEntries: ['/hosts/1'],
    });

    const match = {
      path: '/hosts/:id',
      url: '/hosts/1',
      isExact: true,
    };

    await act(async () => {
      wrapper = await mountWithContexts(<Hosts />, {
        context: { router: { history, route: { match } } },
      });
    });

    expect(wrapper.find('Host').length).toBe(1);
  });
});
