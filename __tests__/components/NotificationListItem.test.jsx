import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import NotificationListItem from '../../src/components/NotificationsList/NotificationListItem';

describe('<NotificationListItem />', () => {
  let wrapper;

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount();
      wrapper = null;
    }
  });

  test('initially renders succesfully', () => {
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem />
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.length).toBe(1);
  });

  test('handles success click when toggle is on', () => {
    const successToggleClickSpy = jest.spyOn(NotificationListItem.prototype, 'successToggleClick');
    const toggleSuccessPropFn = jest.fn();
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            successTurnedOn
            toggleSuccess={toggleSuccessPropFn}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(successToggleClickSpy).toHaveBeenCalledWith(true);
    expect(toggleSuccessPropFn).toHaveBeenCalledWith(9000, true);
  });

  test('handles success click when toggle is off', () => {
    const successToggleClickSpy = jest.spyOn(NotificationListItem.prototype, 'successToggleClick');
    const toggleSuccessPropFn = jest.fn();
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            successTurnedOn={false}
            toggleSuccess={toggleSuccessPropFn}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').first().find('input').simulate('change');
    expect(successToggleClickSpy).toHaveBeenCalledWith(false);
    expect(toggleSuccessPropFn).toHaveBeenCalledWith(9000, false);
  });

  test('handles error click when toggle is on', () => {
    const errorToggleClickSpy = jest.spyOn(NotificationListItem.prototype, 'errorToggleClick');
    const toggleErrorPropFn = jest.fn();
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            errorTurnedOn
            toggleError={toggleErrorPropFn}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(errorToggleClickSpy).toHaveBeenCalledWith(true);
    expect(toggleErrorPropFn).toHaveBeenCalledWith(9000, true);
  });

  test('handles error click when toggle is off', () => {
    const errorToggleClickSpy = jest.spyOn(NotificationListItem.prototype, 'errorToggleClick');
    const toggleErrorPropFn = jest.fn();
    wrapper = mount(
      <I18nProvider>
        <MemoryRouter>
          <NotificationListItem
            itemId={9000}
            errorTurnedOn={false}
            toggleError={toggleErrorPropFn}
          />
        </MemoryRouter>
      </I18nProvider>
    );
    wrapper.find('Switch').at(1).find('input').simulate('change');
    expect(errorToggleClickSpy).toHaveBeenCalledWith(false);
    expect(toggleErrorPropFn).toHaveBeenCalledWith(9000, false);
  });
});
