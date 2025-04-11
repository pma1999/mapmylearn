import { detectBrowserLanguage } from '../components/LanguageSelector';

// Storage key
const LANGUAGE_PREFERENCE_KEY = 'learncompass_language_preference';

/**
 * Save user's language preference to localStorage
 * @param {string} languageCode - ISO language code
 */
export const saveLanguagePreference = (languageCode) => {
  try {
    localStorage.setItem(LANGUAGE_PREFERENCE_KEY, languageCode);
  } catch (error) {
    console.error('Error saving language preference:', error);
  }
};

/**
 * Get user's language preference from localStorage, or detect browser language as fallback
 * @returns {string} ISO language code
 */
export const getLanguagePreference = () => {
  try {
    const savedPreference = localStorage.getItem(LANGUAGE_PREFERENCE_KEY);
    return savedPreference || detectBrowserLanguage();
  } catch (error) {
    console.error('Error getting language preference:', error);
    return 'en'; // Default to English if there's an error
  }
};

/**
 * Clear user's language preference from localStorage
 */
export const clearLanguagePreference = () => {
  try {
    localStorage.removeItem(LANGUAGE_PREFERENCE_KEY);
  } catch (error) {
    console.error('Error clearing language preference:', error);
  }
}; 