import React from 'react';
import {
  Typography,
  Box,
  TextField,
  Button,
  Divider,
  Alert,
  CircularProgress,
} from '@mui/material';
import BoltIcon from '@mui/icons-material/Bolt';
import LanguageSelector from '../../../components/LanguageSelector';
import ApiKeySettings from '../../../components/organisms/ApiKeySettings';
import AdvancedSettings from '../../../components/organisms/AdvancedSettings';
import HistorySettings from '../../../components/organisms/HistorySettings';
import ProgressDisplay from './ProgressDisplay';

/**
 * Form component for the learning path generator
 * @param {Object} props - Component props
 * @param {Object} props.formState - Form state from useGeneratorForm hook
 * @param {Object} props.apiKeyState - API key state from useApiKeyManagement hook
 * @param {Object} props.historyState - History state from useHistoryManagement hook
 * @param {Object} props.progressState - Progress state from useProgressTracking hook
 * @param {boolean} props.isMobile - Whether the display is in mobile viewport
 * @returns {JSX.Element} Generator form component
 */
const GeneratorForm = ({
  formState,
  apiKeyState,
  historyState,
  progressState,
  isMobile
}) => {
  const {
    topic,
    setTopic,
    isGenerating,
    error,
    parallelCount,
    setParallelCount,
    searchParallelCount,
    setSearchParallelCount,
    submoduleParallelCount,
    setSubmoduleParallelCount,
    autoModuleCount,
    setAutoModuleCount,
    desiredModuleCount,
    setDesiredModuleCount,
    autoSubmoduleCount,
    setAutoSubmoduleCount,
    desiredSubmoduleCount,
    setDesiredSubmoduleCount,
    language,
    setLanguage,
    advancedSettingsOpen,
    setAdvancedSettingsOpen,
    apiSettingsOpen,
    setApiSettingsOpen,
    handleSubmit
  } = formState;

  const {
    googleApiKey,
    setGoogleApiKey,
    pplxApiKey,
    setPplxApiKey,
    showGoogleKey,
    setShowGoogleKey,
    showPplxKey,
    setShowPplxKey,
    rememberApiKeys,
    setRememberApiKeys,
    googleKeyValid,
    pplxKeyValid,
    validatingKeys,
    googleKeyToken,
    pplxKeyToken,
    handleValidateApiKeys,
    handleClearApiKeys
  } = apiKeyState;

  const {
    autoSaveToHistory,
    setAutoSaveToHistory,
    initialTags,
    setInitialTags,
    initialFavorite,
    setInitialFavorite,
    newTag,
    setNewTag,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown
  } = historyState;

  const {
    progressUpdates,
    progressPercentage
  } = progressState;

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
      <Alert 
        severity="success" 
        sx={{ 
          mb: 4, 
          '& .MuiAlert-message': { 
            width: '100%'
          } 
        }}
      >
        <Typography variant="subtitle1" fontWeight="bold">
          🎉 New Feature: API Keys Now Provided By Server
        </Typography>
        <Typography variant="body2">
          You no longer need to provide your own API keys! We now provide all required API keys directly from our server.
        </Typography>
      </Alert>

      <Typography
        variant="h4"
        component="h1"
        gutterBottom
        sx={{ 
          fontWeight: 'bold', 
          textAlign: 'center', 
          mb: 3,
          fontSize: { xs: '1.5rem', sm: '2rem', md: '2.125rem' }
        }}
      >
        Generate Learning Path
      </Typography>
      
      <Typography variant="body1" sx={{ 
        mb: 4, 
        textAlign: 'center',
        fontSize: { xs: '0.875rem', sm: '1rem' }
      }}>
        Enter any topic you want to learn about and we'll create a personalized learning path for you.
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <TextField
        label="What do you want to learn about?"
        variant="outlined"
        fullWidth
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Enter a topic (e.g., Machine Learning, Spanish Cooking, Digital Marketing)"
        sx={{ mb: 3 }}
        inputProps={{ maxLength: 100 }}
        required
        disabled={isGenerating}
        autoFocus
      />
      
      <Divider sx={{ my: 3 }} />
      
      {/* Language Selector */}
      <Box sx={{ mt: 2, mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom>
          Content Language
        </Typography>
        <LanguageSelector 
          language={language}
          setLanguage={setLanguage}
        />
      </Box>
      
      {/* Advanced Settings */}
      <AdvancedSettings 
        advancedSettingsOpen={advancedSettingsOpen}
        setAdvancedSettingsOpen={setAdvancedSettingsOpen}
        parallelCount={parallelCount}
        setParallelCount={setParallelCount}
        searchParallelCount={searchParallelCount}
        setSearchParallelCount={setSearchParallelCount}
        submoduleParallelCount={submoduleParallelCount}
        setSubmoduleParallelCount={setSubmoduleParallelCount}
        autoModuleCount={autoModuleCount}
        setAutoModuleCount={setAutoModuleCount}
        desiredModuleCount={desiredModuleCount}
        setDesiredModuleCount={setDesiredModuleCount}
        autoSubmoduleCount={autoSubmoduleCount}
        setAutoSubmoduleCount={setAutoSubmoduleCount}
        desiredSubmoduleCount={desiredSubmoduleCount}
        setDesiredSubmoduleCount={setDesiredSubmoduleCount}
        isGenerating={isGenerating}
        isMobile={isMobile}
      />
      
      {/* API Key Settings */}
      <ApiKeySettings 
        apiSettingsOpen={apiSettingsOpen}
        setApiSettingsOpen={setApiSettingsOpen}
        isMobile={isMobile}
      />
      
      {/* History Settings */}
      <HistorySettings 
        autoSaveToHistory={autoSaveToHistory}
        setAutoSaveToHistory={setAutoSaveToHistory}
        initialFavorite={initialFavorite}
        setInitialFavorite={setInitialFavorite}
        initialTags={initialTags}
        setInitialTags={setInitialTags}
        newTag={newTag}
        setNewTag={setNewTag}
        handleAddTag={handleAddTag}
        handleDeleteTag={handleDeleteTag}
        handleTagKeyDown={handleTagKeyDown}
        isGenerating={isGenerating}
        isMobile={isMobile}
      />
      
      <Box sx={{ 
        display: 'flex', 
        justifyContent: 'center', 
        mt: 3,
        flexDirection: { xs: 'column', sm: 'row' },
        gap: { xs: 2, sm: 0 }
      }}>
        <Button
          type="submit"
          variant="contained"
          color="primary"
          size={isMobile ? "medium" : "large"}
          disabled={isGenerating || !topic.trim()}
          startIcon={isGenerating ? <CircularProgress size={20} color="inherit" /> : <BoltIcon />}
          sx={{ 
            py: { xs: 1, sm: 1.5 }, 
            px: { xs: 2, sm: 4 }, 
            borderRadius: 2, 
            fontWeight: 'bold', 
            fontSize: { xs: '0.9rem', sm: '1.1rem' },
            width: { xs: '100%', sm: 'auto' }
          }}
        >
          {isGenerating ? 'Generating...' : 'Generate Learning Path'}
        </Button>
      </Box>
      
      {/* Progress display (shown when generating) */}
      {isGenerating && (
        <ProgressDisplay 
          progressUpdates={progressUpdates}
          progressPercentage={progressPercentage}
          isMobile={isMobile}
        />
      )}
    </Box>
  );
};

export default GeneratorForm; 