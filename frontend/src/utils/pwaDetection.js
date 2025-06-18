/**
 * Comprehensive PWA Detection Utility
 * Provides browser detection, device detection, and PWA capability analysis
 */

/**
 * Detects the current browser type
 * @returns {string} Browser identifier: 'safari', 'chrome', 'firefox', 'edge', 'unknown'
 */
export const detectBrowser = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (userAgent.includes('edg/')) return 'edge';
  if (userAgent.includes('chrome') && !userAgent.includes('edg/')) return 'chrome';
  if (userAgent.includes('firefox')) return 'firefox';
  if (userAgent.includes('safari') && !userAgent.includes('chrome')) return 'safari';
  
  return 'unknown';
};

/**
 * Detects the current device type
 * @returns {string} Device identifier: 'ios', 'android', 'desktop'
 */
export const detectDevice = () => {
  const userAgent = navigator.userAgent.toLowerCase();
  
  if (/ipad|iphone|ipod/.test(userAgent)) return 'ios';
  if (/android/.test(userAgent)) return 'android';
  
  return 'desktop';
};

/**
 * Checks if the browser supports PWA installation prompts
 * @returns {boolean} Whether installation prompts are supported
 */
export const checkInstallPromptSupport = () => {
  // Check for beforeinstallprompt event support (Chrome, Edge)
  if ('onbeforeinstallprompt' in window) return true;
  
  // Check for service worker support (basic PWA requirement)
  if ('serviceWorker' in navigator) return true;
  
  return false;
};

/**
 * Attempts to detect if PWA is already installed
 * @returns {boolean} Best-effort detection of PWA installation status
 */
export const checkPWAInstallation = () => {
  // Check for standalone mode (iOS Safari, some Android browsers)
  if (window.matchMedia('(display-mode: standalone)').matches) return true;
  
  // Check for navigator.standalone (iOS Safari specific)
  if ('standalone' in navigator && navigator.standalone) return true;
  
  // Check for related applications (newer browsers)
  if ('getInstalledRelatedApps' in navigator) {
    // This is async, but we'll handle it separately for real-time detection
    return false; // Conservative fallback
  }
  
  return false;
};

/**
 * Comprehensive PWA capabilities detection
 * @returns {Object} Complete PWA context information
 */
export const detectPWACapabilities = () => {
  const browser = detectBrowser();
  const device = detectDevice();
  const isInstallable = checkInstallPromptSupport();
  const isInstalled = checkPWAInstallation();
  const supportsServiceWorker = 'serviceWorker' in navigator;
  
  return {
    browser,
    device,
    isInstallable,
    isInstalled,
    supportsServiceWorker,
    // Derived capabilities
    showInstallInstructions: !isInstalled && (isInstallable || device !== 'desktop'),
    canUseOffline: supportsServiceWorker,
    needsManualInstall: device === 'ios' && browser === 'safari',
  };
};

/**
 * Async function to check installed related apps (for supported browsers)
 * @returns {Promise<boolean>} Promise resolving to installation status
 */
export const checkInstalledRelatedApps = async () => {
  if ('getInstalledRelatedApps' in navigator) {
    try {
      const relatedApps = await navigator.getInstalledRelatedApps();
      return relatedApps.length > 0;
    } catch (error) {
      console.warn('Could not check installed related apps:', error);
      return false;
    }
  }
  return false;
};

/**
 * Gets browser-specific installation method
 * @param {string} browser Browser type from detectBrowser()
 * @param {string} device Device type from detectDevice()  
 * @returns {string} Installation method identifier
 */
export const getInstallationMethod = (browser, device) => {
  if (device === 'ios' && browser === 'safari') return 'safari_ios';
  if (device === 'android' && browser === 'chrome') return 'chrome_android';
  if (device === 'desktop' && browser === 'chrome') return 'chrome_desktop';
  if (device === 'desktop' && browser === 'edge') return 'edge_desktop';
  if (browser === 'firefox') return 'firefox_manual';
  
  return 'generic';
};

/**
 * Utility to track tutorial completion
 * @param {string} version Tutorial version identifier
 * @returns {Object} Tutorial tracking utilities
 */
export const createTutorialTracker = (version) => {
  const storageKey = `mapmylearn_pwa_intro_${version}`;
  
  return {
    hasCompleted: () => localStorage.getItem(storageKey) === 'completed',
    markCompleted: () => localStorage.setItem(storageKey, 'completed'),
    reset: () => localStorage.removeItem(storageKey),
    getStorageKey: () => storageKey,
  };
}; 