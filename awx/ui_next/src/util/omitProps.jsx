import React from 'react';

export default function omitProps(Component, ...omit) {
  return function Omit(props) {
    const clean = { ...props };
    omit.forEach(key => {
      delete clean[key];
    })
    return <Component {...clean} />;
  }
}
