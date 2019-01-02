import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import api from '../../src/api';
import { API_CONFIG } from '../../src/endpoints';
import About from '../../src/components/About';

describe('<About />', () => {
  let aboutWrapper;
  let closeButton;

  test('initially renders without crashing', () => {
    aboutWrapper = mount(
      <I18nProvider>
        <About isOpen />
      </I18nProvider>
    );
    expect(aboutWrapper.length).toBe(1);
    aboutWrapper.unmount();
  });

  test('close button calls onAboutModalClose', () => {
    const onAboutModalClose = jest.fn();
    aboutWrapper = mount(
      <I18nProvider>
        <About isOpen onAboutModalClose={onAboutModalClose} />
      </I18nProvider>
    );
    closeButton = aboutWrapper.find('AboutModalBoxCloseButton Button');
    closeButton.simulate('click');
    expect(onAboutModalClose).toBeCalled();
    aboutWrapper.unmount();
  });
});
