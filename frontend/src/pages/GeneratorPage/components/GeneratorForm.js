import React, { useState } from 'react';
import {
  Typography,
  Box,
  TextField,
  Button,
  Divider,
  CircularProgress,
  Alert,
  Chip,
  Tooltip
} from '@mui/material';
import BoltIcon from '@mui/icons-material/Bolt';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import TokenIcon from '@mui/icons-material/Token';
import LanguageSelector from '../../../components/LanguageSelector';
import AdvancedSettings from '../../../components/organisms/AdvancedSettings';
import { useAuth } from '../../../services/authContext';
import { helpTexts } from '../../../constants/helpTexts';
import CreditPurchaseDialog from '../../../components/payments/CreditPurchaseDialog';

/**
 * Form component for the learning path generator
 * @param {Object} props - Component props
 * @param {Object} props.formState - Form state from useGeneratorForm hook
 * @param {Object} props.progressState - Progress state from useProgressTracking hook
 * @param {boolean} props.isMobile - Whether the display is in mobile viewport
 * @returns {JSX.Element} Generator form component
 */
const GeneratorForm = ({
  formState,
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

  // Get user and credits
  const { user } = useAuth();
  const [purchaseDialogOpen, setPurchaseDialogOpen] = useState(false);

  const hasCredits = user?.credits > 0;
  const creditsNeeded = 1; // Define cost

  const handleOpenPurchaseDialog = () => {
     setPurchaseDialogOpen(true);
  };

  const handleClosePurchaseDialog = () => {
     setPurchaseDialogOpen(false);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
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
        <AutoAwesomeIcon sx={{ mr: 1, verticalAlign: 'middle', fontSize: { xs: '1.8rem', sm: '2.2rem' } }} />
        Generate Learning Path
      </Typography>
      
      <Typography variant="body1" sx={{ 
        mb: 4, 
        textAlign: 'center',
        fontSize: { xs: '0.875rem', sm: '1rem' }
      }}>
        Enter any topic you want to learn about and we'll create a personalized learning path for you.
      </Typography>
      
      {/* Display error from generation submission */}
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
          disabled={isGenerating}
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
      
      {/* Action Buttons Area */}
      <Box sx={{ 
        mt: 3,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 2
      }}>
        {/* Conditionally show alert if no credits */}
        {!hasCredits && !isGenerating && (
          <Alert 
             severity="warning" 
             sx={{ width: '100%', mb: 1 }} 
             action={
               <Button color="inherit" size="small" onClick={handleOpenPurchaseDialog}>
                 Buy Credits
               </Button>
             }
           >
             You need credits to generate a learning path.
          </Alert>
        )}

        {/* Generate Button */} 
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          width: '100%', 
          flexDirection: { xs: 'column', sm: 'row' }, 
          alignItems: 'center', 
          gap: 1 // Add gap between button and hint
        }}>
          <Button
            type="submit"
            variant="contained"
            color="primary"
            size={isMobile ? "medium" : "large"}
            disabled={isGenerating || !topic.trim() || !hasCredits} // Disable if no credits
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

          {/* Credit Cost Hint */} 
          <Tooltip title="Generating a new learning path costs 1 credit.">
             <Chip 
               icon={<TokenIcon fontSize="small" />} 
               label={helpTexts.generatorCostHint} 
               size="small" 
               variant="outlined" 
             />
          </Tooltip>
        </Box>
      </Box>

       {/* Purchase Dialog */}
       <CreditPurchaseDialog
         open={purchaseDialogOpen}
         onClose={handleClosePurchaseDialog}
       />
    </Box>
  );
};

export default GeneratorForm; 