import React from 'react';
import { FormControl, InputLabel, MenuItem, Select, Box, Tooltip } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';

// Importamos las imágenes de banderas (usaremos URL públicas en CDN para este ejemplo)
const FLAG_BASE_URL = 'https://flagcdn.com/16x12';

// Language options with ISO codes, names and flag image paths
const LANGUAGE_OPTIONS = [
  { code: 'en', name: 'English', flagUrl: `${FLAG_BASE_URL}/gb.png` },
  { code: 'es', name: 'Español', flagUrl: `${FLAG_BASE_URL}/es.png` },
  { code: 'fr', name: 'Français', flagUrl: `${FLAG_BASE_URL}/fr.png` },
  { code: 'de', name: 'Deutsch', flagUrl: `${FLAG_BASE_URL}/de.png` },
  { code: 'it', name: 'Italiano', flagUrl: `${FLAG_BASE_URL}/it.png` },
  { code: 'pt', name: 'Português', flagUrl: `${FLAG_BASE_URL}/pt.png` },
  { code: 'zh', name: '中文', flagUrl: `${FLAG_BASE_URL}/cn.png` },
  { code: 'ja', name: '日本語', flagUrl: `${FLAG_BASE_URL}/jp.png` },
  { code: 'ru', name: 'Русский', flagUrl: `${FLAG_BASE_URL}/ru.png` },
];

// Detect browser language for initial default
const detectBrowserLanguage = () => {
  try {
    const browserLang = navigator.language || navigator.userLanguage;
    const langCode = browserLang.split('-')[0];
    
    // Check if detected language is in our options
    const isSupported = LANGUAGE_OPTIONS.some(lang => lang.code === langCode);
    return isSupported ? langCode : 'en'; // Default to English if not supported
  } catch (error) {
    console.error('Error detecting browser language:', error);
    return 'en'; // Default to English on error
  }
};

const LanguageSelector = ({ language, setLanguage, sx = {}, disabled = false }) => {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', ...sx }}>
      <FormControl variant="outlined" size="small" fullWidth disabled={disabled}>
        <InputLabel id="language-select-label">Language</InputLabel>
        <Select
          labelId="language-select-label"
          id="language-select"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          label="Language"
          sx={{ minWidth: 120 }}
          disabled={disabled}
        >
          {LANGUAGE_OPTIONS.map((lang) => (
            <MenuItem key={lang.code} value={lang.code}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <img 
                  src={lang.flagUrl} 
                  alt={`${lang.name} flag`}
                  style={{ 
                    marginRight: 8,
                    width: 16,
                    height: 12,
                    objectFit: 'cover',
                    boxShadow: '0 0 1px rgba(0,0,0,0.2)'
                  }} 
                />
                {lang.name}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Tooltip
        title="Select the language for your learning path content. Note: Search will still use the most information-rich language for your topic (typically English)."
        placement="top"
        arrow
      >
        <InfoIcon sx={{ ml: 1, color: 'text.secondary', fontSize: 20 }} />
      </Tooltip>
    </Box>
  );
};

export { LANGUAGE_OPTIONS, detectBrowserLanguage };
export default LanguageSelector; 