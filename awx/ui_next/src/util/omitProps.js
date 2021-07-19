import React from 'react';

/*
 * Prevents styled-components from passing down an unsupported
 * props to children, resulting in console warnings.
 * https://github.com/styled-components/styled-components/issues/439
 */
export default function omitProps(Component, ...omit) {
  return function Omit(props) {
    const clean = { ...props };
    omit.forEach(key => {
      delete clean[key];
    });
    return <Component {...clean} />;
  };
}
