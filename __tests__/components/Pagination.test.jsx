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
    const pageSizeDropdownItemsSelector = 'DropdownItem button';
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
    expect(onSetPage).toBeCalledWith(1, 25);
  });

  test('itemCount displays correctly', () => {
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={7}
          page={1}
          pageCount={2}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    let itemCount = pagination.find('.awx-pagination__item-count');
    expect(itemCount.text()).toEqual('Items 1 – 5 of 7');

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={7}
          page={2}
          pageCount={2}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    itemCount = pagination.find('.awx-pagination__item-count');
    expect(itemCount.text()).toEqual('Items 6 – 7 of 7');
  });

  test('itemCount matching pageSize displays correctly', () => {
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={5}
          page={1}
          pageCount={1}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    const itemCount = pagination.find('.awx-pagination__item-count');
    expect(itemCount.text()).toEqual('Items 1 – 5 of 5');
  });

  test('itemCount less than pageSize displays correctly', () => {
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={3}
          page={1}
          pageCount={1}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    const itemCount = pagination.find('.awx-pagination__item-count');
    expect(itemCount.text()).toEqual('Items 1 – 3 of 3');
  });

  test('submitting a new page by typing in input works', () => {
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
    const paginationElem = pagination.find('Pagination');
    expect(paginationElem.state().value).toBe(1);
    const textInput = pagination.find(textInputSelector);
    expect(textInput.length).toBe(1);
    expect(textInput.at(0).prop('value')).toBe(1);
    const input = pagination.find('TextInput');
    expect(input.prop('value')).toBe(1);
    input.prop('onChange')(2);
    pagination.update();
    const submitForm = pagination.find(submitFormSelector);
    expect(submitForm.length).toBe(1);
    submitForm.simulate('submit');
    expect(pagination.find('TextInput').prop('value')).toBe(2);
    // assert onPageChange was called
    expect(paginationElem.state().value).toBe(2);
  });

  test('submitting a new page by typing in input does not work when invalid', () => {
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
    const paginationElem = pagination.find('Pagination');
    expect(paginationElem.state().value).toBe(1);
    const textInput = pagination.find(textInputSelector);
    expect(textInput.length).toBe(1);
    expect(textInput.at(0).prop('value')).toBe(1);
    const input = pagination.find('TextInput');
    expect(input.prop('value')).toBe(1);
    input.prop('onChange')('!invalid');
    pagination.update();
    const submitForm = pagination.find(submitFormSelector);
    expect(submitForm.length).toBe(1);
    submitForm.simulate('submit');
    expect(pagination.find('TextInput').prop('value')).toBe(1);
    // assert onPageChange was not called
    expect(paginationElem.state().value).toBe(1);
  });

  test('text input page change is not displayed when only 1 page', () => {
    const onSetPage = jest.fn();
    const pageNumber = 'input[aria-label="Page Number"]';
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
    let pageInput = pagination.find(pageNumber);
    expect(pageInput.length).toBe(0);

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={11}
          page={1}
          pageCount={3}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    pageInput = pagination.find(pageNumber);
    expect(pageInput.length).toBe(1);
  });

  test('make sure componentDidUpdate calls onPageChange', () => {
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={7}
          page={1}
          pageCount={2}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    const paginationElem = pagination.find('Pagination');
    expect(paginationElem.state().value).toBe(1);
    pagination.setProps({
      children: (
        <Pagination
          count={7}
          page={2}
          pageCount={2}
          page_size={5}
          pageSizeOptions={[5, 10, 25, 50]}
          onSetPage={onSetPage}
        />
      )
    });
    paginationElem.update();
    expect(paginationElem.state().value).toBe(2);
  });

  test('when showPageSizeOptions is passed as false there should not be a dropdown in the DOM', () => {
    const pageSizeDropdownSelector = '.awx-pagination__page-size-selection';
    const onSetPage = jest.fn();

    pagination = mount(
      <I18nProvider>
        <Pagination
          count={21}
          page={1}
          pageCount={5}
          page_size={5}
          showPageSizeOptions={false}
          onSetPage={onSetPage}
        />
      </I18nProvider>
    );
    const pageSizeDropdown = pagination.find(pageSizeDropdownSelector);
    expect(pageSizeDropdown.length).toBe(0);
  });
});
