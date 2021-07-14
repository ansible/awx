import React from 'react';
import { shallow } from 'enzyme';
import Jobs from './Jobs';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: () => ({
    path: '/',
  }),
}));

describe('<Jobs />', () => {
  test('initially renders successfully', async () => {
    const wrapper = shallow(<Jobs />);
    expect(wrapper.find('JobList')).toHaveLength(1);
  });

  test('should display a breadcrumb heading', () => {
    const wrapper = shallow(<Jobs />);
    const screenHeader = wrapper.find('ScreenHeader');
    expect(screenHeader).toHaveLength(1);
    expect(screenHeader.prop('breadcrumbConfig')).toEqual({
      '/jobs': 'Jobs',
    });
  });
});
