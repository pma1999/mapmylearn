import { createContext, useContext } from 'react';

const PwaIntroContext = createContext(null);

export const usePwaIntro = () => {
  const context = useContext(PwaIntroContext);
  if (!context) {
    throw new Error('usePwaIntro must be used within a PwaIntroContext provider');
  }
  return context;
};

export default PwaIntroContext;
