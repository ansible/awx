import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

jest.mock('react-dom', () => ({ render: jest.fn() }));

const div = document.createElement('div');
div.setAttribute('id', 'app');
document.body.appendChild(div);

require('./index.jsx');

describe('index.jsx', () => {
  it('renders ok', () => {
    expect(ReactDOM.render).toHaveBeenCalledWith(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
      div
    );
  });
});
