import React from 'react';
import { shallow, mount } from 'enzyme';
import App from '../src/App';
import api from '../src/api';
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
});
