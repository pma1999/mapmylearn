import React from 'react';
import { useParams, useNavigate } from 'react-router';
import {
  Box,
  CircularProgress,
  Typography,
  Paper,
  Container,
  Alert,
  Button,
  Grid,
  Chip,
  Tooltip,
  Skeleton,
  LinearProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HourglassEmptyIcon from '@mui/icons-material/HourglassEmpty';
import ArticleIcon from '@mui/icons-material/Article';
import OndemandVideoIcon from '@mui/icons-material/OndemandVideo';
import LinkIcon from '@mui/icons-material/Link';
import QuizIcon from '@mui/icons-material/Quiz';
import SearchIcon from '@mui/icons-material/Search';
import DnsIcon from '@mui/icons-material/Dns';
import TocIcon from '@mui/icons-material/Toc';
import FolderZipIcon from '@mui/icons-material/FolderZip';
import HistoryIcon from '@mui/icons-material/History';

import useProgressTracking from '../../components/learning-path/hooks/useProgressTracking';
import { useAuth } from '../../services/authContext';
import { useTheme } from '@mui/material/styles';

// --- Curiosities Components ---
import { CuriosityCarousel } from './components/Curiosities';
// --- Refined Blueprint View Components ---

const StatusIndicator = ({ status, size = 12 }) => {
  let color = 'action.disabled';
  let Icon = HourglassEmptyIcon;

  if (status === 'defined' || status === 'planned') {
    color = 'info.main';
    Icon = DnsIcon;
  } else if (status?.includes('loading') || status?.includes('started') || status?.includes('processing') || status === 'pending') {
    color = 'warning.main';
    Icon = HourglassEmptyIcon;
  } else if (status === 'completed' || status?.includes('completed') || status === 'fully_processed') {
    color = 'success.main';
    Icon = CheckCircleOutlineIcon;
  } else if (status === 'error' || status?.includes('error') || status === 'skipped') {
    color = 'error.main';
    Icon = ErrorOutlineIcon;
  }

  return (
    <Tooltip title={`Status: ${status || 'unknown'}`}>
      <Icon sx={{ color, fontSize: size, verticalAlign: 'middle' }} />
    </Tooltip>
  );
};

const ResourceChip = ({ type, title, url, variant = "outlined", size="small" }) => {
  let icon = <LinkIcon fontSize="inherit" />;
  if (type?.toLowerCase().includes('article') || type?.toLowerCase().includes('text')) icon = <ArticleIcon fontSize="inherit" />;
  if (type?.toLowerCase().includes('video')) icon = <OndemandVideoIcon fontSize="inherit" />;
  
  return (
    <Tooltip title={`${type}: ${title} - ${url}`}>
        <Chip 
            icon={icon}
            label={title ? title.substring(0, 30) + (title.length > 30 ? '...' : '') : 'Resource'}
            size={size}
            variant={variant}
            onClick={() => url && window.open(url, '_blank')}
            clickable={!!url}
            sx={{ mr: 0.5, mb: 0.5, maxWidth: 180 }}
        />
    </Tooltip>
  );
}

const ResourcePreviewDisplay = ({ count, status, resources_preview = [], typeLabel = "Resources" }) => {
  if (status === 'pending') return <Chip size="small" label={`${typeLabel}: Pending`} icon={<HourglassEmptyIcon fontSize="inherit"/>} variant="outlined" sx={{mr:1, my:0.5}} />;
  if (status === 'loading') return <Chip size="small" label={`${typeLabel}: Finding...`} icon={<CircularProgress size={14} thickness={5}/>} variant="outlined" sx={{mr:1, my:0.5}} />;
  if (status === 'completed' && count > 0) {
    return (
        <Accordion variant="outlined" elevation={0} sx={{width: '100%', '& .MuiAccordionSummary-root': {minHeight: '36px', p:0.5}, '& .MuiAccordionDetails-root': {p:1}}}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ '.MuiAccordionSummary-content': { my: 0, alignItems: 'center'} }}>
                <Chip size="small" label={`${typeLabel}: ${count} found`} color="primary" variant="outlined" />
            </AccordionSummary>
            <AccordionDetails sx={{display: 'flex', flexWrap: 'wrap'}}>
                {resources_preview.map((res, i) => <ResourceChip key={i} {...res} />)}
                {count > resources_preview.length && <Chip size="small" label={`+${count - resources_preview.length} more`} variant="ghost"/>}
            </AccordionDetails>
        </Accordion>
    );
  }
  if (status === 'completed' && count === 0) return <Chip size="small" label={`${typeLabel}: None Found`} variant="outlined" sx={{mr:1, my:0.5}} />;
  if (status === 'error') return <Chip size="small" label={`${typeLabel}: Error`} color="error" variant="outlined" sx={{mr:1, my:0.5}}/>;
  return null;
};

const SubmoduleItem = ({ submodule }) => {
  const [expanded, setExpanded] = React.useState(false);
  return (
    <Paper variant="outlined" sx={{ p: 1.5, mb: 1, '&:hover': {borderColor: 'primary.main'} }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }} onClick={() => setExpanded(!expanded)}>
            <Box sx={{display: 'flex', alignItems: 'center'}}>
                <StatusIndicator status={submodule.status} size={20}/>
                <Typography variant="subtitle1" sx={{ml: 1}}>{submodule.title || <Skeleton width="150px" />}</Typography>
            </Box>
            <ExpandMoreIcon sx={{ transform: expanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}/>
        </Box>
        {submodule.status && !submodule.status.includes("planned") && !submodule.status.includes("defined") && 
            <LinearProgress variant="determinate" value={submodule.status === 'completed' || submodule.status === 'fully_processed' ? 100 : (submodule.status?.includes('quiz') ? 75 : (submodule.status?.includes('content') ? 50 : 25))} sx={{my:1, height:2, borderRadius:1}}/>
        }
        {expanded && (
            <Box sx={{pl: 3.5, pt:1}}>
                {submodule.descriptionPreview && <Typography variant="caption" color="text.secondary" display="block" gutterBottom>{submodule.descriptionPreview}</Typography>}
                <Box sx={{display: 'flex', alignItems: 'center', flexWrap:'wrap', gap:1, mt:1}}>
                    <ResourcePreviewDisplay 
                        count={submodule.resourceCount} 
                        status={submodule.resourceStatus} 
                        resources_preview={submodule.resources_preview} 
                    />
                    {submodule.quiz_question_count > 0 && 
                        <Chip size="small" label={`Quiz: ${submodule.quiz_question_count} questions`} icon={<QuizIcon fontSize="inherit"/>} variant="outlined" />}
                    {submodule.error && <Alert severity='error' variant='caption' sx={{fontSize: '0.75rem', p:0.5}}>{submodule.error}</Alert>}
                </Box>
            </Box>
        )}
    </Paper>
  );
};

const ModuleItem = ({ moduleData, defaultExpanded = false }) => {
  return (
    <Paper elevation={3} sx={{ p: {xs:1.5, sm:2}, mb: 2, borderRadius: 2 }}>
      <Accordion defaultExpanded={defaultExpanded} sx={{boxShadow:'none', '&:before': {display:'none'}, '&.Mui-expanded': {margin:0}}}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{p: {xs:0, sm:1}, '& .MuiAccordionSummary-content': { alignItems: 'center' } }}>
            <StatusIndicator status={moduleData.status} size={24} />
            <Typography variant="h6" component="div" sx={{ ml: 1.5, flexGrow: 1 }}>
                {moduleData.title || <Skeleton width="70%" />}
            </Typography>
        </AccordionSummary>
        <AccordionDetails sx={{p: {xs:0.5, sm:1.5}}}>
            {moduleData.descriptionPreview && <Typography variant="body2" color="text.secondary" gutterBottom sx={{mb:2}}>{moduleData.descriptionPreview}</Typography>}
            <ResourcePreviewDisplay 
                count={moduleData.resourceCount} 
                status={moduleData.resourceStatus} 
                resources_preview={moduleData.resources_preview}
            />
            <Box mt={1.5}>
            {moduleData.submodules && moduleData.submodules.length > 0 
                ? moduleData.submodules.sort((a,b) => (a.order || 0) - (b.order || 0)).map((sm, idx) => <SubmoduleItem key={sm.id || `sm-${idx}`} submodule={sm} />)
                : (
                    <Box sx={{textAlign: 'center', my: 2}}>
                        <CircularProgress size={24} sx={{mr:1}}/>
                        <Typography variant="body2" color="text.secondary" component="span">Planning submodules...</Typography>
                    </Box>
                )}
            </Box>
        </AccordionDetails>
      </Accordion>
    </Paper>
  );
};

const BlueprintView = ({ liveBuildData }) => {
  if (!liveBuildData || !liveBuildData.modules) {
    return (
        <Paper elevation={2} sx={{ p: 3, mt: 3, textAlign: 'center', borderRadius: 2 }}>
            <CircularProgress sx={{mb: 2}}/>
            <Typography variant="h6">Waiting for course structure to initialize...</Typography>
            <Typography variant="body2" color="text.secondary">This typically starts within a few seconds.</Typography>
        </Paper>
    );
  }

  const topic = liveBuildData.topic || sessionStorage.getItem('currentTopic') || "Your Course";

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h4" component="h2" gutterBottom sx={{textAlign: 'center', fontWeight: 500, mb:1}}>
        Blueprint: <Typography component="span" variant="h4" color="primary">{topic}</Typography>
      </Typography>
      
      <Paper elevation={1} sx={{p:2, mb:3, borderRadius: 2}}>
        <Typography variant="h6" gutterBottom sx={{display: 'flex', alignItems:'center'}}><FolderZipIcon sx={{mr:1, color: 'primary.main'}}/>Topic Resources</Typography>
        <ResourcePreviewDisplay 
            count={liveBuildData.topicResources?.count || 0} 
            status={liveBuildData.topicResources?.status || 'pending'} 
            resources_preview={liveBuildData.topicResources?.resources_preview}
            typeLabel="Overall Topic Resources"
        />
      </Paper>

      {liveBuildData.searchQueries && liveBuildData.searchQueries.length > 0 && (
        <Paper variant="outlined" sx={{ p: 1.5, mb: 3, borderRadius: 2 }}>
          <Typography variant="subtitle1" gutterBottom sx={{display: 'flex', alignItems:'center'}}><SearchIcon sx={{mr:1}}/>Initial Search Strategy</Typography>
          <Box sx={{display: 'flex', flexWrap: 'wrap', gap: 1}}>
            {liveBuildData.searchQueries.map((sq, i) => <Chip key={i} label={sq.text} size="small" variant="outlined"/>)}
          </Box>
        </Paper>
      )}

      {liveBuildData.modules && liveBuildData.modules.length > 0 
        ? liveBuildData.modules.sort((a,b) => (a.order || 0) - (b.order || 0)).map((mod, idx) => (
            <ModuleItem key={mod.id || `mod-${idx}`} moduleData={mod} defaultExpanded={idx === 0} />
          ))
        : (
            <Paper elevation={2} sx={{p:3, textAlign:'center', borderRadius:2}}>
                <CircularProgress sx={{mb:1}}/>
                <Typography variant="body1" color="text.secondary">Module structure is being defined by AI...</Typography>
            </Paper>
        )
      }
    </Box>
  );
};

const OverallProgressDisplay = ({ overallProgress, overallStatusMessage, topic }) => {
  return (
    <Paper elevation={3} sx={{ mb: 3, p: {xs:2, sm:3}, borderRadius: 2, textAlign: 'center' }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{fontWeight: 'bold', fontSize: {xs: '2rem', sm: '2.5rem', md: '3rem'} }}>
        Crafting: <Typography component="span" variant="inherit" color="primary">{topic}</Typography>
      </Typography>
      {overallStatusMessage && 
        <Typography variant="subtitle1" color="text.secondary" gutterBottom sx={{minHeight: '2.2em', display:'flex', alignItems:'center', justifyContent:'center'}}>
          <CircularProgress size={16} sx={{mr: 1, visibility: overallProgress < 1 && overallProgress > 0 ? 'visible': 'hidden'}}/> 
          {overallStatusMessage}
        </Typography>
      }
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1.5, mt: 2, width: '100%', maxWidth: 400, margin: 'auto' }}>
        <Box sx={{ width: '100%', mr: 1 }}>
             <LinearProgress variant={overallProgress > 0 ? "determinate" : "indeterminate"} value={overallProgress * 100} sx={{height: 10, borderRadius: 5}} />
        </Box>
        <Typography variant="h6" color="text.primary" sx={{minWidth: '45px'}}>{`${Math.round((overallProgress || 0) * 100)}%`}</Typography>
      </Box>
    </Paper>
  )
}

const LeavePageNotice = ({ taskId, overallProgress, user, onHistoryClick }) => {
  const [dismissed, setDismissed] = React.useState(false);
  const storageKey = React.useMemo(() => `mml_leave_notice_dismissed_${user?.id || 'anon'}_${taskId}`, [user?.id, taskId]);

  React.useEffect(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved === 'true') setDismissed(true);
    } catch {}
  }, [storageKey]);

  if ((overallProgress || 0) >= 1 || dismissed) return null;

  const handleDismiss = () => {
    try { localStorage.setItem(storageKey, 'true'); } catch {}
    setDismissed(true);
  };

  const text = 'You can leave now — your course will keep generating in the background. Check its status anytime in History.';
  const historyLabel = 'Open History';
  const dismissLabel = 'Dismiss';

  return (
    <Alert
      severity="info"
      variant="outlined"
      icon={<HistoryIcon />}
      sx={{ mb: 2, borderRadius: 2 }}
      action={
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button color="primary" size="small" onClick={onHistoryClick}>{historyLabel}</Button>
          <Button size="small" onClick={handleDismiss}>{dismissLabel}</Button>
        </Box>
      }
    >
      <Typography variant="body2">{text}</Typography>
    </Alert>
  );
};

const GeneratingPage = () => {
  const { taskId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const handleTaskComplete = (taskResult) => {
    if (taskResult.status === 'completed' && taskResult.result) {
      navigate(`/result/${taskId}`);
    } else if (taskResult.status === 'failed') {
      console.error("Task failed in GeneratingPage:", taskResult.error);
    }
  };

  const { 
    progressMessages, 
    taskStatus, 
    liveBuildData, 
    overallProgress, 
    error: taskLevelError
  } = useProgressTracking(taskId, handleTaskComplete);

  const currentTopic = liveBuildData?.topic || sessionStorage.getItem('currentTopic') || 'your new course';
  const currentOverallStatusMessage = liveBuildData?.overallStatusMessage || 
                               (progressMessages.length > 0 ? progressMessages[progressMessages.length - 1].message : 'Initializing generation process...');

  if (!user) {
    navigate('/login');
    return null;
  }

  if (taskStatus === 'failed') {
    const errorMessage = taskLevelError?.message || 
                         liveBuildData?.error?.message || 
                         'An unknown error occurred during generation. Please check the logs or try again later.';
    return (
      <Container maxWidth="md" sx={{ py: 4, textAlign: 'center' }}>
        <Paper elevation={3} sx={{ p: {xs: 2, sm: 4}, borderRadius: 2 }}>
          <ErrorOutlineIcon sx={{fontSize: 60, color: 'error.main', mb:2}}/>
          <Typography variant="h4" color="error.dark" gutterBottom>Course Generation Failed</Typography>
          <Alert severity="error" sx={{textAlign: 'left', mt:1, mb:3}}>{errorMessage}</Alert>
          <Button variant="contained" onClick={() => navigate('/')} sx={{ mr:1 }}>Try New Topic</Button>
          <Button variant="outlined" onClick={() => navigate(`/result/${taskId}`)} title="May show partial or error state">View Last State (if any)</Button>
        </Paper>
      </Container>
    );
  }
  
  if (!taskStatus && !liveBuildData?.modules?.length && overallProgress === 0) {
      return (
        <Container maxWidth="sm" sx={{display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 'calc(100vh - 120px)' }}>
            <CircularProgress size={60} />
            <Typography variant="h6" sx={{ mt: 3, textAlign: 'center' }}>
                Preparing your course blueprint for "{currentTopic}"...             
            </Typography>
             <Typography variant="body2" color="text.secondary" sx={{mt:1}}>This may take a few moments to connect and initialize.</Typography>
        </Container>
      );
  }

  const curiosities = liveBuildData?.curiosityFeed?.status === 'ready' ? (liveBuildData.curiosityFeed.items || []) : [];

  return (
    <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 3 } }}>
      <OverallProgressDisplay 
        overallProgress={overallProgress || (liveBuildData?.overallProgress || 0)} 
        overallStatusMessage={currentOverallStatusMessage}
        topic={currentTopic}
      />
      <LeavePageNotice 
        taskId={taskId}
        overallProgress={overallProgress || (liveBuildData?.overallProgress || 0)}
        user={user}
        onHistoryClick={() => navigate('/history')}
      />
      {/* Curiosities Carousel */}
      <CuriosityCarousel items={curiosities} autoplay={(overallProgress || 0) < 1} />
      <BlueprintView liveBuildData={liveBuildData} />
    </Container>
  );
};

export default GeneratingPage; 