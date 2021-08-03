import React from 'react';
import { createMemoryHistory } from 'history';
import { shallow } from 'enzyme';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Applications from './Applications';

describe('<Applications />', () => {
  let wrapper;

  test('renders successfully', () => {
    wrapper = mountWithContexts(<Applications />);
    const pageSections = wrapper.find('PageSection');
    expect(wrapper.length).toBe(1);
    expect(pageSections.length).toBe(1);
    expect(pageSections.first().props().variant).toBe('light');
  });

  test('shows Application information modal after successful creation', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/applications/add'],
    });
    wrapper = shallow(<Applications />, {
      context: { router: { history } },
    });
    expect(wrapper.find('Modal[title="Application information"]').length).toBe(
      0
    );
    wrapper.find('ApplicationAdd').props().onSuccessfulAdd({
      name: 'test',
      client_id: 'foobar',
      client_secret: 'aaaaaaaaaaaaaaaaaaaaaaaaaa',
    });
    wrapper.update();
    expect(wrapper.find('Modal[title="Application information"]').length).toBe(
      1
    );
  });
});
