import React from 'react';
import { mount } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import Pagination from '../../src/components/Pagination';

describe('<Pagination />', () => {
  let pagination;

  afterEach(() => {
    if (pagination) {
      pagination.unmount();
      pagination = null;
    }
  });

  test('it triggers the expected callbacks on next and last', () => {
    const next = 'button[aria-label="Next"]';
    const last = 'button[aria-label="Last"]';

    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={1}
          pageCount={5}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );

    pagination.find(next).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(1);
    expect(onSetPage).toBeCalledWith(2, 5);

    pagination.find(last).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(2);
    expect(onSetPage).toBeCalledWith(5, 5);
  });

  test('it triggers the expected callback on previous and first', () => {
    const previous = 'button[aria-label="Previous"]';
    const first = 'button[aria-label="First"]';

    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={5}
          pageCount={5}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );

    pagination.find(previous).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(1);
    expect(onSetPage).toBeCalledWith(4, 5);

    pagination.find(first).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(2);
    expect(onSetPage).toBeCalledWith(1, 5);
  });

  test('previous button does not work on page 1', () => {
    const previous = 'button[aria-label="First"]';
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={1}
          pageCount={5}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    pagination.find(previous).simulate('click');
    expect(onSetPage).toHaveBeenCalledTimes(0);
  });

  test('changing pageSize works', () => {
    const pageSizeDropdownToggleSelector = 'DropdownToggle DropdownToggle[className="togglePageSize"]';
    const pageSizeDropdownItemsSelector = 'DropdownItem';
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={1}
          pageCount={5}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    const pageSizeDropdownToggle = pagination.find(pageSizeDropdownToggleSelector);
    expect(pageSizeDropdownToggle.length).toBe(1);
    pageSizeDropdownToggle.at(0).simulate('click');

    const pageSizeDropdownItems = pagination.find(pageSizeDropdownItemsSelector);
    expect(pageSizeDropdownItems.length).toBe(3);
    pageSizeDropdownItems.at(1).simulate('click');
  });

  test('submit a new page by typing in input works', () => {
    const textInputSelector = '.awx-pagination__page-input.pf-c-form-control';
    const submitFormSelector = '.awx-pagination__page-input-form';
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={1}
          pageCount={5}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );

    const textInput = pagination.find(textInputSelector);
    expect(textInput.length).toBe(1);
    textInput.simulate('change');
    pagination.setProps({ page: 2 });

    const submitForm = pagination.find(submitFormSelector);
    expect(submitForm.length).toBe(1);
    submitForm.simulate('submit');
    pagination.find('Pagination').instance().setState({ value: 'invalid' });
    submitForm.simulate('submit');
  });

  test('text input page change is disabled when only 1 page', () => {
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={4}
          page={1}
          pageCount={1}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
  });
});
