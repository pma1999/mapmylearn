import { createContext, useContext } from 'react';

const PwaIntroContext = createContext(null);

export const usePwaIntro = () => {
  const context = useContext(PwaIntroContext);
  if (!context) {
    throw new Error('usePwaIntro must be used within a PwaIntroContext provider');
  }
  return context;
};

/**
 * Enhanced PWA Introduction Context
 * 
 * Provides access to PWA tutorial functionality and capabilities across the app.
 * 
 * Context Value Structure:
 * {
 *   openPwaIntro: () => void,           // Function to manually open the PWA tutorial
 *   pwaCapabilities: {                  // PWA detection results
 *     browser: string,                  // Browser type: 'safari', 'chrome', 'firefox', 'edge', 'unknown'
 *     device: string,                   // Device type: 'ios', 'android', 'desktop'  
 *     isInstallable: boolean,           // Whether PWA installation is supported
 *     isInstalled: boolean,             // Whether PWA is currently installed
 *     supportsServiceWorker: boolean,   // Whether service workers are supported
 *     showInstallInstructions: boolean, // Whether to show installation instructions
 *     canUseOffline: boolean,           // Whether offline features are available
 *     needsManualInstall: boolean       // Whether manual install steps are required
 *   },
 *   tutorialTracker: {                  // Tutorial completion tracking
 *     hasCompleted: () => boolean,      // Check if tutorial is completed
 *     markCompleted: () => void,        // Mark tutorial as completed
 *     reset: () => void,                // Reset tutorial completion status
 *     getStorageKey: () => string       // Get the storage key for the current version
 *   }
 * }
 */

export default PwaIntroContext;
