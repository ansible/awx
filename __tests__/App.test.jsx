import React from 'react';
import { shallow, mount } from 'enzyme';
import App from '../src/App';
import api from '../src/api';
import * as constant from '../src/endpoints';

import Dashboard from '../src/pages/Dashboard';
import Login from '../src/pages/Login';
import { asyncFlush } from '../jest.setup';

const DEFAULT_ACTIVE_GROUP = 'views_group';
const DEFAULT_ACTIVE_ITEM = 'views_group_dashboard';

describe('<App />', () => {
  test('renders without crashing', () => {
    const appWrapper = shallow(<App />);
    expect(appWrapper.length).toBe(1);
  });

  test('renders login page when not authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(false);

    const appWrapper = mount(<App />);

    const login = appWrapper.find(Login);
    expect(login.length).toBe(1);
    const dashboard = appWrapper.find(Dashboard);
    expect(dashboard.length).toBe(0);
  });

  test('renders dashboard when authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(true);

    const appWrapper = mount(<App />);

    const dashboard = appWrapper.find(Dashboard);
    expect(dashboard.length).toBe(1);
    const login = appWrapper.find(Login);
    expect(login.length).toBe(0);
  });

  test('onNavSelect sets state.activeItem and state.activeGroup', () => {
    const appWrapper = shallow(<App />);
    appWrapper.instance().onNavSelect({ itemId: 'foo', groupId: 'bar' });
    expect(appWrapper.state().activeItem).toBe('foo');
    expect(appWrapper.state().activeGroup).toBe('bar');
  });

  test('onNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = shallow(<App />);
    expect(appWrapper.state().isNavOpen).toBe(true);
    appWrapper.instance().onNavToggle();
    expect(appWrapper.state().isNavOpen).toBe(false);
  });

  test('onLogoClick sets selected nav back to defaults', () => {
    const appWrapper = shallow(<App />);
    appWrapper.setState({ activeGroup: 'foo', activeItem: 'bar' });
    expect(appWrapper.state().activeItem).toBe('bar');
    expect(appWrapper.state().activeGroup).toBe('foo');
    appWrapper.instance().onLogoClick();
    expect(appWrapper.state().activeItem).toBe(DEFAULT_ACTIVE_ITEM);
    expect(appWrapper.state().activeGroup).toBe(DEFAULT_ACTIVE_GROUP);
  });

  test('api.logout called from logout button', async () => {
    api.BaseGet = jest.fn().mockImplementation(() => Promise.resolve({}));
    const appWrapper = mount(<App />);
    const logoutButton = appWrapper.find('LogoutButton');
    logoutButton.props().onDevLogout();
    appWrapper.setState({ activeGroup: 'foo', activeItem: 'bar' });
    expect(api.BaseGet).toHaveBeenCalledTimes(1);
    expect(api.BaseGet).toHaveBeenCalledWith(constant.API_LOGOUT);
    await asyncFlush();
    expect(appWrapper.state().activeItem).toBe(DEFAULT_ACTIVE_ITEM);
    expect(appWrapper.state().activeGroup).toBe(DEFAULT_ACTIVE_GROUP);
  });
});
