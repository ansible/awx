import { useEffect, useState } from 'react';
import ReactDOM from 'react-dom';

function AppendBody({ children }) {
  const [el] = useState(document.createElement('div'));

  useEffect(() => {
    document.body.appendChild(el);
    return () => {
      document.body.removeChild(el);
    };
  }, [el]);

  return ReactDOM.createPortal(children, el);
}

export default AppendBody;
