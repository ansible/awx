import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import LogoutButton from '../../src/components/LogoutButton';

let buttonWrapper;
let buttonElem;
let userIconElem;

const findChildren = () => {
  buttonElem = buttonWrapper.find('Button');
  userIconElem = buttonWrapper.find('UserIcon');
};

describe('<LogoutButton />', () => {
  test('initially renders without crashing', () => {
    const onDevLogout = jest.fn();
    buttonWrapper = mount(
      <I18nProvider>
        <LogoutButton onDevLogout={onDevLogout} />
      </I18nProvider>
    );
    findChildren();
    expect(buttonWrapper.length).toBe(1);
    expect(buttonElem.length).toBe(1);
    expect(userIconElem.length).toBe(1);
    buttonElem.simulate('keyDown', { keyCode: 40, which: 40 });
    expect(onDevLogout).toHaveBeenCalledTimes(0);
    buttonElem.simulate('keyDown', { keyCode: 13, which: 13 });
    expect(onDevLogout).toHaveBeenCalledTimes(1);
  });
});
