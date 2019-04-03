import React from 'react';

export default function FormRow ({ children }) {
  return (
    <div
      style={{
        display: 'grid',
        gridGap: '20px',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))'
      }}
    >
      {children}
    </div>
  );
}
