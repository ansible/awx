import React from 'react';
import { mount } from 'enzyme';
import Pagination from '../../src/components/Pagination';

describe('<Pagination />', () => {
  const noop = () => {};

  let pagination;

  afterEach(() => {
    if (toolbar) {
      pagination.unmount();
      pagination = null;
    }
  });

  test('it triggers the expected callbacks on next and last', () => {
    const next = 'button[aria-label="next"]';
    const last = 'button[aria-label="last"]';

    const onSetPage = jest.fn();

    pagination = mount(
      <Pagination
        count={21}
        page={1}
        pageCount={5}
        page_size={5}
        pageSizeOptions={[5, 10, 25, 50]}
        onSetPage={onSetPage}
      />
    );

    pagination.find(next).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(1);
    expect(onSetPage).toBeCalledWith(2, 5);

    pagination.find(last).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(2);
    expect(onSetPage).toBeCalledWith(5, 5);
  });

  test('it triggers the expected callback on previous and first', () => {
    const previous = 'button[aria-label="previous"]';
    const first = 'button[aria-label="first"]';

    const onSetPage = jest.fn();

    pagination = mount(
      <Pagination
        count={21}
        page={5}
        pageCount={5}
        page_size={5}
        pageSizeOptions={[5, 10, 25, 50]}
        onSetPage={onSetPage}
      />
    );

    pagination.find(previous).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(1);
    expect(onSetPage).toBeCalledWith(4, 5);

    pagination.find(first).simulate('click');

    expect(onSetPage).toHaveBeenCalledTimes(2);
    expect(onSetPage).toBeCalledWith(1, 5);
  });
});
