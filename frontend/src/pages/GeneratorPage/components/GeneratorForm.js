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
  Tooltip,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import BoltIcon from '@mui/icons-material/Bolt';
import AutoAwesomeIcon from '@mui/icons-material/AutoAwesome';
import TokenIcon from '@mui/icons-material/Token';
import LanguageSelector from '../../../components/LanguageSelector';
import AdvancedSettings from '../../../components/organisms/AdvancedSettings';
import { useAuth } from '../../../services/authContext';
import { helpTexts } from '../../../constants/helpTexts';
import CreditPurchaseDialog from '../../../components/payments/CreditPurchaseDialog';

// Icons for Explanation Styles
import ArticleOutlinedIcon from '@mui/icons-material/ArticleOutlined';
import LightbulbOutlinedIcon from '@mui/icons-material/LightbulbOutlined';
import PrecisionManufacturingOutlinedIcon from '@mui/icons-material/PrecisionManufacturingOutlined';
import ListAltOutlinedIcon from '@mui/icons-material/ListAltOutlined';
import AccountTreeOutlinedIcon from '@mui/icons-material/AccountTreeOutlined';
import PsychologyAltIcon from '@mui/icons-material/PsychologyAlt';

// Import FormHelperText
import FormHelperText from '@mui/material/FormHelperText';

/**
 * Descriptions for each explanation style.
 */
const styleDescriptions = {
  standard: "Balanced, clear, and informative explanations suitable for a general audience. Uses standard terminology.",
  simple: "Uses straightforward language, avoids jargon, focuses on core ideas, and may use basic analogies. Ideal for beginners or complex topics.",
  technical: "Uses precise, formal, and technical terminology. Explores details, mechanisms, and underlying principles. Assumes some foundational knowledge.",
  example: "Explains concepts primarily through practical examples, code snippets (if applicable), case studies, or real-world scenarios.",
  conceptual: "Focuses on the high-level ideas, the 'why' behind concepts, connections between different topics, and underlying principles, rather than implementation details.",
  grumpy_genius: "Accurate explanations delivered with comedic reluctance and intellectual sighs, as if forced by a brilliant but easily exasperated expert."
};

/**
 * Form component for the course generator
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
    explanationStyle,
    setExplanationStyle,
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
        Generate Course
      </Typography>
      
      <Typography variant="body1" sx={{ 
        mb: 4, 
        textAlign: 'center',
        fontSize: { xs: '0.875rem', sm: '1rem' }
      }}>
        Enter any topic you want to learn about and we'll create a personalized course for you.
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
      
      {/* Explanation Style Selector */}
      <Box sx={{ mt: 2, mb: 3 }}>
        <FormControl fullWidth variant="outlined" disabled={isGenerating}>
          <InputLabel id="explanation-style-label">Explanation Style</InputLabel>
          <Select
            labelId="explanation-style-label"
            id="explanation-style-select"
            value={explanationStyle}
            label="Explanation Style"
            onChange={(e) => setExplanationStyle(e.target.value)}
            sx={{ '.MuiSelect-select': { display: 'flex', alignItems: 'center' } }}
          >
            <MenuItem value="standard">
              <ArticleOutlinedIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Standard
            </MenuItem>
            <MenuItem value="simple">
              <LightbulbOutlinedIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Simple & Clear
            </MenuItem>
            <MenuItem value="technical">
              <PrecisionManufacturingOutlinedIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Technical Deep Dive
            </MenuItem>
            <MenuItem value="example">
              <ListAltOutlinedIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Learn by Example
            </MenuItem>
            <MenuItem value="conceptual">
              <AccountTreeOutlinedIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Big Picture Focus
            </MenuItem>
            <MenuItem value="grumpy_genius">
              <PsychologyAltIcon sx={{ mr: 1.5, verticalAlign: 'middle' }} fontSize="small" />
              Grumpy Genius Mode
            </MenuItem>
          </Select>
          <FormHelperText sx={{ mt: 1 }}>
            {styleDescriptions[explanationStyle]}
          </FormHelperText>
        </FormControl>
      </Box>
      
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
             You need credits to generate a course.
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
            {isGenerating ? 'Generating...' : 'Generate Course'}
          </Button>

          {/* Credit Cost Hint */} 
          <Tooltip title="Generating a new course costs 1 credit.">
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