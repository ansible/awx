import { locales } from '../../i18nLoader';
import { act } from '@testing-library/react';
import LanguageFilter from './LanguageFilter';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

describe('LanguageFilter', () => {
  let wrapper;
  const { location } = window;

  beforeAll(() => {
    Object.defineProperty(window, 'location', {
      configurable: true,
      value: { reload: jest.fn() },
    });
  });

  test('open language toolbar', async () => {
    await act(async () => {
      wrapper = mountWithContexts(<LanguageFilter />);
    });

    await act(async () => {
      wrapper.find('button[aria-label="Language"]').simulate('click');
    });

    await act(async () => {
      wrapper.update();
      wrapper.find('ul[role="menu"]').first().simulate('click');
      expect(wrapper.find('DropdownItem')).toHaveLength(
        Object.keys(locales).length + 2
      );
      expect(
        wrapper
          .find('button[data-ouia-component-id="reset-to-browser-defaults"]')
          .prop('aria-disabled')
      ).toBe(true);
    });
  });

  test('select one language', async () => {
    await act(async () => {
      wrapper.update();
      wrapper
        .find('button[data-ouia-component-id="lang-dropdown-fr"]')
        .simulate('click');
    });

    await act(async () => {
      wrapper.update();
      expect(wrapper.find('DropdownItem')).toHaveLength(0);
    });
  });

  test('check reset to defaults enabled', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Language"]').simulate('click');
    });

    await act(async () => {
      wrapper.update();
      wrapper.find('ul[role="menu"]').first().simulate('click');
    });

    await act(async () => {
      wrapper.update();
      expect(
        wrapper
          .find('button[data-ouia-component-id="reset-to-browser-defaults"]')
          .prop('aria-disabled')
      ).toBe(false);
    });
  });
  window.location = location;
});
