import React, { Component } from 'react';
import {
  Route,
  Redirect
} from 'react-router-dom';
import { shallow } from 'enzyme';
import ConditionalRedirect from '../../src/components/ConditionalRedirect';

describe('<ConditionalRedirect />', () => {
  test('renders Redirect when shouldRedirect is passed truthy func', () => {
    const truthyFunc = () => true;
    const shouldHaveRedirectChild = shallow(<ConditionalRedirect shouldRedirect={() => truthyFunc()} />);
    const redirectChild = shouldHaveRedirectChild.find(Redirect);
    expect(redirectChild.length).toBe(1);
    const routeChild = shouldHaveRedirectChild.find(Route);
    expect(routeChild.length).toBe(0);
  });

  test('renders Route when shouldRedirect is passed falsy func', () => {
    const falsyFunc = () => false;
    const shouldHaveRouteChild = shallow(<ConditionalRedirect shouldRedirect={() => falsyFunc()} />);
    const routeChild = shouldHaveRouteChild.find(Route);
    expect(routeChild.length).toBe(1);
    const redirectChild = shouldHaveRouteChild.find(Redirect);
    expect(redirectChild.length).toBe(0);
  });
});