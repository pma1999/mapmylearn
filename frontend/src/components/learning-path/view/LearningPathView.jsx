import React, { useRef } from 'react';
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router';
import { Container, Snackbar, Alert, AlertTitle, Box, Button } from '@mui/material';
import { helpTexts } from '../../../constants/helpTexts';
import LoginIcon from '@mui/icons-material/Login';

// Custom hooks
import useLearningPathView from '../hooks/useLearningPathView';

// View components
import LearningPathHeader from './LearningPathHeader';
import LoadingState from './LoadingState';
import ErrorState from './ErrorState';
import SaveDialog from './SaveDialog';
import ResourcesSection from '../../shared/ResourcesSection';
import ModuleNavigationColumn from './ModuleNavigationColumn';
import ContentPanel from './ContentPanel';
import MobileBottomNavigation from './MobileBottomNavigation.jsx';
import CourseOverview from './CourseOverview';

// Layout components
import ResponsiveLayout from '../components/ResponsiveLayout';
import ViewModeLayout from '../components/ViewModeLayout';
import TutorialComponent from '../components/TutorialComponent';

/**
 * Main component for viewing a course using the Focus Flow layout.
 * 
 * @param {Object} props Component props
 * @param {string} props.source Source of the course ('history', 'public' or null/undefined for generation)
 * @returns {JSX.Element} course view component
 */
const LearningPathView = ({ source }) => {
  const navigate = useNavigate();
  const contentPanelRef = useRef(null);

  // Use our comprehensive hook that manages all state and logic
  const {
    // Core data
    learningPath,
    actualPathData,
    topic,
    topicResources,
    loading,
    error,

    // Navigation data
    modules,
    totalModules,
    currentModule,
    totalSubmodulesInModule,
    currentSubmodule,
    derivedPathId,

    // State
    activeModuleIndex,
    activeSubmoduleIndex,
    contentPanelDisplayType,
    activeTab,
    setActiveTab,
    viewMode,
    switchToOverview,
    switchToFocus,
    availableTabs,
    findTabIndex,
    progressMap,

    // Flags
    isFromHistory,
    isPublicView,
    isTemporaryPath,
    isPdfReady,
    isPublic,
    isAuthenticated,
    isMobileLayout,
    isMobile,
    showFirstViewAlert,
    isCopying,
    mobileNavOpen,
    localDetailsHaveBeenSet,

    // IDs
    currentEntryId,
    relevantShareIdForHeader,

    // Actions from useLearningPathActions
    saveDialogOpen,
    tags,
    newTag,
    favorite,
    notification,
    handleDownloadPDF, // Extract the handler
    handleSaveToHistory,
    handleSaveOffline, // Extract the handler
    handleSaveDialogClose,
    handleSaveConfirm,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    handleNotificationClose,
    setNewTag,
    setFavorite,
    handleHomeClick,
    handleNewLearningPathClick,

    // Sharing actions
    handleTogglePublic,
    handleCopyShareLink,

    // Navigation handlers
    handleNavigation,
    selectSubmodule,
    selectModuleResources,
    toggleModule,
    handleSelectSubmoduleFromOverview,
    handleStartCourse,

    // Handlers
    handleToggleProgress,
    handleCopyToHistory,
    handleDismissFirstViewAlert,
    handleMobileNavToggle,
    handleMobileNavClose,
    handleSubmoduleSelectFromDrawer,

    // Tutorial
    runTutorial,
    tutorialStepIndex,
    tutorialSteps,
    startTutorial,
    handleJoyrideCallback,

    // Theme
    theme,

    // CourseView specific (for compatibility)
    progressMessages,
    isReconnecting,
    retryAttempt
  } = useLearningPathView(source, {
    includeVisualization: true,
    initialViewMode: 'overview',
    enableTutorial: true
  });

  // Adjusted download handlers
  const handleDownloadJSONAdjusted = () => {
    if (!actualPathData) return;
    try {
      const json = JSON.stringify(actualPathData, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = topic 
        ? `course_${topic.replace(/\s+/g, '_').substring(0, 30)}.json`
        : 'course.json';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading JSON:', err);
    }
  };

  // Loading state
  if (loading) {
    return (
      <LoadingState 
        topic={learningPath?.topic || sessionStorage.getItem('currentTopic')}
        // CourseView specific props
        progressMessages={progressMessages}
        isReconnecting={isReconnecting}
        retryAttempt={retryAttempt}
      />
    );
  }

  // Error state
  if (error) {
    return (
      <ErrorState 
        error={error || 'An error occurred'} 
        onHomeClick={handleHomeClick}
        onNewLearningPathClick={handleNewLearningPathClick}
      />
    );
  }

  // Main render
  return (
    <Container 
      maxWidth="xl" 
      sx={{ 
        pt: { xs: 2, md: 3 }, 
        pb: { 
          xs: `calc(${theme.spacing(8)} + env(safe-area-inset-bottom, 0px))`,
          md: theme.spacing(4) 
        }, 
        display: 'flex', 
        flexDirection: 'column', 
        flexGrow: 1 
      }}
    >
      {/* First view alert */}
      {showFirstViewAlert && (
        <Alert 
          severity="info" 
          sx={{ mb: 2, flexShrink: 0 }} 
          onClose={handleDismissFirstViewAlert}
        >
          <AlertTitle>Your Course is Ready!</AlertTitle>
          {helpTexts.lpFirstViewAlert}
        </Alert>
      )}

      {/* Public view login prompt */}
      {isPublicView && !isAuthenticated && (
        <Alert 
          severity="info" 
          sx={{ mb: 2, flexShrink: 0 }} 
          action={
            <Box>
              <Button color="inherit" size="small" onClick={() => navigate('/login')} startIcon={<LoginIcon/>}>
                Log In
              </Button>
              <Button color="inherit" size="small" onClick={() => navigate('/register')}>
                Sign Up
              </Button>
            </Box>
          }
        >
          <AlertTitle>Explore More!</AlertTitle>
          Log in or sign up to save this course, track your progress, and create your own learning journeys.
        </Alert>
      )}

      {learningPath && (
        <>
          {/* Header */}
          <Box sx={{ flexShrink: 0, mb: { xs: 2, md: 3 } }}>
            <LearningPathHeader 
              topic={topic} 
              detailsHaveBeenSet={localDetailsHaveBeenSet} 
              isPdfReady={isPdfReady} 
              onDownload={handleDownloadJSONAdjusted} 
              onDownloadPDF={handleDownloadPDF} // Pass the real handler
              onSaveToHistory={handleSaveToHistory}
              onSaveOffline={handleSaveOffline} // Pass the real handler
              onNewLearningPath={handleNewLearningPathClick}
              onOpenMobileNav={handleMobileNavToggle} 
              showMobileNavButton={isMobileLayout && viewMode === 'focus'} 
              progressMap={progressMap}
              actualPathData={actualPathData} 
              onStartTutorial={startTutorial} 
              isPublicView={isPublicView} 
              isPublic={isPublic} 
              shareId={relevantShareIdForHeader} 
              entryId={currentEntryId} 
              isLoggedIn={isAuthenticated} 
              onTogglePublic={() => handleTogglePublic(currentEntryId, !isPublic)} 
              onCopyShareLink={handleCopyShareLink} 
              onCopyToHistory={handleCopyToHistory} 
              isCopying={isCopying} 
              viewMode={viewMode}
              onBackToOverview={switchToOverview}
            />

            {/* Topic Resources Section */}
            {topicResources && topicResources.length > 0 && (
              <Box sx={{ mt: 2 }} data-tut="topic-resources-section">
                <ResourcesSection
                  resources={topicResources}
                  title="Overall Course Resources"
                  type="topic"
                  collapsible={true}
                  expanded={false}
                  compact={false}
                />
              </Box>
            )}
          </Box>

          {/* Main Content Area */}
          <ViewModeLayout
            viewMode={viewMode}
            overviewComponent={
              <CourseOverview
                actualPathData={actualPathData}
                topic={topic}
                topicResources={topicResources}
                onSelectSubmodule={handleSelectSubmoduleFromOverview}
                onStartCourse={handleStartCourse}
                progressMap={progressMap}
                onToggleProgress={handleToggleProgress}
                isPublicView={isPublicView}
              />
            }
            focusComponent={
              <ResponsiveLayout
                isMobileLayout={isMobileLayout}
                theme={theme}
                mobileNavOpen={mobileNavOpen}
                onMobileNavClose={handleMobileNavClose}
                drawerTitle="Modules"
                navigationComponent={
                  <ModuleNavigationColumn
                    modules={actualPathData?.modules || []} 
                    activeModuleIndex={activeModuleIndex}
                    onModuleClick={toggleModule} // Pass the correct handler
                    activeSubmoduleIndex={activeSubmoduleIndex}
                    selectSubmodule={selectSubmodule} 
                    onSelectModuleResources={selectModuleResources} 
                    contentPanelDisplayType={contentPanelDisplayType}
                    progressMap={progressMap}
                    onToggleProgress={handleToggleProgress}
                    isPublicView={isPublicView}
                    onSubmoduleSelect={handleSubmoduleSelectFromDrawer}
                  />
                }
                contentComponent={
                  <ContentPanel
                    ref={contentPanelRef}
                    sx={{ height: '100%' }}
                    displayType={contentPanelDisplayType}
                    module={currentModule}
                    moduleIndex={activeModuleIndex}
                    submodule={currentSubmodule}
                    submoduleIndex={activeSubmoduleIndex}
                    pathId={derivedPathId}
                    isTemporaryPath={isTemporaryPath}
                    actualPathData={actualPathData} 
                    onNavigate={handleNavigation}
                    totalModules={totalModules}
                    totalSubmodulesInModule={totalSubmodulesInModule}
                    isMobileLayout={isMobileLayout}
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    progressMap={progressMap}
                    onToggleProgress={handleToggleProgress}
                    isPublicView={isPublicView}
                  />
                }
                mobileBottomNavigation={
                  <MobileBottomNavigation 
                    onNavigate={handleNavigation}
                    activeModuleIndex={activeModuleIndex}
                    activeSubmoduleIndex={activeSubmoduleIndex}
                    totalModules={totalModules}
                    totalSubmodulesInModule={totalSubmodulesInModule}
                    activeTab={activeTab}
                    setActiveTab={setActiveTab}
                    availableTabs={availableTabs} 
                    onOpenMobileNav={handleMobileNavToggle}
                    contentPanelDisplayType={contentPanelDisplayType}
                  />
                }
              />
            }
          />
        </>
      )}

      {/* Tutorial */}
      <TutorialComponent
        steps={tutorialSteps}
        run={runTutorial}
        stepIndex={tutorialStepIndex}
        callback={handleJoyrideCallback}
        theme={theme}
      />

      {/* Save Dialog */}
      {!isPublicView && (
        <SaveDialog
          open={saveDialogOpen}
          onClose={handleSaveDialogClose}
          onConfirm={handleSaveConfirm} 
          tags={tags} 
          newTag={newTag} 
          favorite={favorite} 
          onAddTag={handleAddTag} 
          onDeleteTag={handleDeleteTag} 
          onTagChange={setNewTag} 
          onTagKeyDown={handleTagKeyDown} 
          onFavoriteChange={setFavorite} 
          isMobile={isMobile} 
        />
      )}

      {/* Notifications */}
      {notification && notification.open && (
        <Snackbar
          open={notification.open}
          autoHideDuration={6000}
          onClose={handleNotificationClose}
          anchorOrigin={{ 
            vertical: 'bottom', 
            horizontal: isMobile ? 'center' : 'right' 
          }}
          sx={{
            bottom: { xs: `calc(${theme.spacing(2)} + env(safe-area-inset-bottom, 0px))`, sm: theme.spacing(3) },
          }}
        >
          <Alert 
            onClose={handleNotificationClose} 
            severity={notification.severity}
            elevation={6} 
            variant="filled" 
            sx={{ width: '100%' }} 
          >
            {notification.message}
          </Alert>
        </Snackbar>
      )}
    </Container>
  );
};

LearningPathView.propTypes = {
  source: PropTypes.oneOf(['history', 'public', 'offline', null, undefined]),
};

export default LearningPathView;
