import React from 'react';
import { Container, Paper, Divider, Grid, Snackbar, Alert, useMediaQuery, useTheme } from '@mui/material';

// Custom hooks
import useNotification from './hooks/useNotification';
import useHistoryFilters from './hooks/useHistoryFilters';
import useHistoryEntries from './hooks/useHistoryEntries';
import useHistoryActions from './hooks/useHistoryActions';

// Components
import PageHeader from './components/PageHeader';
import HistoryFilters from './components/HistoryFilters';
import HistoryEntryCard from './components/HistoryEntryCard';
import HistoryEntrySkeleton from './components/HistoryEntrySkeleton';
import EmptyState from './components/EmptyState';
import ImportDialog from './components/ImportDialog';
import ConfirmationDialog from './components/ConfirmationDialog';

/**
 * History page component for displaying and managing learning path history
 * @returns {JSX.Element} History page component
 */
const HistoryPage = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
  // Initialize notification hook
  const { 
    notification, 
    showNotification, 
    closeNotification 
  } = useNotification();
  
  // Initialize filters hook
  const {
    sortBy,
    filterSource,
    searchTerm,
    handleSortChange,
    handleFilterChange,
    handleSearchChange,
    clearFilters
  } = useHistoryFilters();
  
  // Initialize history entries hook with filter options
  const {
    entries,
    loading,
    refreshEntries
  } = useHistoryEntries(
    { sortBy, filterSource, searchTerm },
    showNotification
  );
  
  // Initialize history actions hook
  const {
    importDialogOpen,
    setImportDialogOpen,
    clearHistoryDialog,
    setClearHistoryDialog,
    handleViewLearningPath,
    handleDeleteLearningPath,
    handleToggleFavorite,
    handleUpdateTags,
    handleExportLearningPath,
    handleDownloadPDF,
    handleExportAllHistory,
    handleImportLearningPath,
    handleClearHistory
  } = useHistoryActions(showNotification, refreshEntries);
  
  // Computed value to check if any filters are applied
  const hasFiltersApplied = !!filterSource || !!searchTerm || sortBy !== 'creation_date';
  
  return (
    <Container maxWidth="lg">
      <Paper elevation={3} sx={{ p: { xs: 2, sm: 3, md: 4 }, borderRadius: 2, mb: 4 }}>
        <PageHeader 
          hasEntries={entries.length > 0}
          onImport={() => setImportDialogOpen(true)}
          onExport={handleExportAllHistory}
          onClear={() => setClearHistoryDialog(true)}
        />
        
        <Divider sx={{ mb: 3 }} />
        
        <HistoryFilters
          sortBy={sortBy}
          onSortChange={handleSortChange}
          filterSource={filterSource}
          onFilterChange={handleFilterChange}
          search={searchTerm}
          onSearchChange={handleSearchChange}
        />
        
        {loading ? (
          <Grid container spacing={2}>
            <HistoryEntrySkeleton count={6} />
          </Grid>
        ) : entries.length > 0 ? (
          <Grid container spacing={2}>
            {entries.map((entry) => (
              <HistoryEntryCard
                key={entry.id || entry.path_id}
                entry={entry}
                onView={handleViewLearningPath}
                onDelete={handleDeleteLearningPath}
                onToggleFavorite={handleToggleFavorite}
                onUpdateTags={handleUpdateTags}
                onExport={handleExportLearningPath}
                onDownloadPDF={handleDownloadPDF}
              />
            ))}
          </Grid>
        ) : (
          <EmptyState 
            onClearFilters={hasFiltersApplied ? clearFilters : undefined}
            hasFilters={hasFiltersApplied}
          />
        )}
      </Paper>
      
      {/* Import Dialog */}
      <ImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onImport={handleImportLearningPath}
      />
      
      {/* Clear History Confirmation Dialog */}
      <ConfirmationDialog
        open={clearHistoryDialog}
        title="Clear All History"
        message="Are you sure you want to delete all learning paths? This action cannot be undone."
        onConfirm={handleClearHistory}
        onCancel={() => setClearHistoryDialog(false)}
      />
      
      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={closeNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default HistoryPage; 