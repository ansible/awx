import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { shallow, mount } from 'enzyme';
import App from '../src/App';
import api from '../src/api';
import { API_LOGOUT, API_CONFIG } from '../src/endpoints';

import Dashboard from '../src/pages/Dashboard';
import Login from '../src/pages/Login';

describe('<App />', () => {
  test('renders without crashing', () => {
    const appWrapper = shallow(<App />);
    expect(appWrapper.length).toBe(1);
  });

  test('renders login page when not authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(false);

    const appWrapper = mount(<MemoryRouter><App /></MemoryRouter>);

    const login = appWrapper.find(Login);
    expect(login.length).toBe(1);
    const dashboard = appWrapper.find(Dashboard);
    expect(dashboard.length).toBe(0);
  });

  test('renders dashboard when authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(true);

    const appWrapper = mount(<MemoryRouter><App /></MemoryRouter>);

    const dashboard = appWrapper.find(Dashboard);
    expect(dashboard.length).toBe(1);
    const login = appWrapper.find(Login);
    expect(login.length).toBe(0);
  });

  test('onNavToggle sets state.isNavOpen to opposite', () => {
    const appWrapper = shallow(<App.WrappedComponent />);
    expect(appWrapper.state().isNavOpen).toBe(true);
    appWrapper.instance().onNavToggle();
    expect(appWrapper.state().isNavOpen).toBe(false);
  });

  test('api.logout called from logout button', async () => {
    const logOutButtonSelector = 'button[aria-label="Logout"]';
    api.get = jest.fn().mockImplementation(() => Promise.resolve({}));
    const appWrapper = mount(<MemoryRouter><App /></MemoryRouter>);
    const logOutButton = appWrapper.find(logOutButtonSelector);
    expect(logOutButton.length).toBe(1);
    logOutButton.simulate('click');
    appWrapper.setState({ activeGroup: 'foo', activeItem: 'bar' });
    expect(api.get).toHaveBeenCalledWith(API_LOGOUT);
  });

  test('Componenet makes REST call to API_CONFIG endpoint when mounted', () => {
    api.get = jest.fn().mockImplementation(() => Promise.resolve({}));
    const appWrapper = shallow(<App.WrappedComponent />);
    expect(api.get).toHaveBeenCalledTimes(1);
    expect(api.get).toHaveBeenCalledWith(API_CONFIG);
  });
});
