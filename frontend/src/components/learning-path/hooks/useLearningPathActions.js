import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router';
import {
  saveToHistory,
  updateHistoryEntry,
  downloadLearningPathPDF,
  getHistoryEntry,
  downloadLearningPathMarkdown,
} from '../../../services/api';
import { saveOfflinePath } from '../../../services/offlineService';
import { buildSelectiveMarkdown, createSelectiveFilename, validateSelection } from '../../../utils/selectiveMarkdownBuilder';

/**
 * Custom hook for managing actions related to a course
 * 
 * @param {Object} learningPath - The course data
 * @param {boolean} isFromHistory - Whether the course is from history
 * @param {boolean} detailsHaveBeenSet - Whether tags/favorites have been set for the path
 * @param {string} entryId - ID of the history entry (if from history or after save)
 * @param {string} taskId - ID of the task (if from generation)
 * @param {string} temporaryPathId - Newly added temporary ID (if applicable)
 * @param {Function} onSaveSuccess - Callback function invoked after successful save
 * @returns {Object} Actions and states for course management
 */
const useLearningPathActions = (
  learningPath, 
  isFromHistory, 
  detailsHaveBeenSet,
  entryId, 
  taskId,
  temporaryPathId,
  onSaveSuccess
) => {
  const navigate = useNavigate();
  
  // States
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [selectiveExportDialogOpen, setSelectiveExportDialogOpen] = useState(false);
  const [tags, setTags] = useState([]);
  const [newTag, setNewTag] = useState('');
  const [favorite, setFavorite] = useState(false);
  const [notification, setNotification] = useState({ 
    open: false, 
    message: '', 
    severity: 'info' 
  });

  /**
   * Shows a notification message
   * @param {string} message - Message to display
   * @param {string} severity - Severity level (success, error, warning, info)
   */
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  /**
   * Closes the notification
   */
  const handleNotificationClose = () => {
    setNotification({ ...notification, open: false });
  };

  /**
   * Downloads the course as JSON
   */
  const handleDownloadJSON = () => {
    if (!learningPath) return;
    
    try {
      const json = JSON.stringify(learningPath, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      
      const a = document.createElement('a');
      a.href = url;
      const fileName = learningPath.topic 
        ? `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.json`
        : 'learning_path.json';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('Learning path downloaded successfully', 'success');
    } catch (err) {
      console.error('Error downloading JSON:', err);
      showNotification('Failed to download course', 'error');
    }
  };

  /**
   * Downloads the course as PDF
   */
  const handleDownloadPDF = async () => {
    if (!learningPath) return;

    // Ensure we have the correct ID. Priority: history entryId
    // The entryId prop passed to this hook IS the correct one after saving
    const targetId = entryId; 

    if (!targetId) {
      // This should ideally not happen if the button is correctly disabled
      // when !isPersisted, but as a safeguard:
      console.error("PDF Download Error: Cannot download PDF without a valid History Entry ID.");
      showNotification('Please save the course to history first', 'error');
      return { savedToHistory: false }; 
    }

    try {
      // Show loading notification
      showNotification('Generating PDF...', 'info');

      // Download the PDF using the history entry ID
      const pdfBlob = await downloadLearningPathPDF(targetId);
      
      // Create a download link
      const url = URL.createObjectURL(pdfBlob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = learningPath.topic 
        ? `learning_path_${learningPath.topic.replace(/\\s+/g, '_').substring(0, 30)}.pdf`
        : 'learning_path.pdf';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showNotification('PDF downloaded successfully', 'success');
      return { savedToHistory: true };
    } catch (err) {
      console.error('Error downloading PDF:', err);
      showNotification('Failed to download PDF', 'error');
      return { savedToHistory: false };
    }
  };

  /**
   * Downloads the course as Markdown.
   * Uses backend for persisted entries; otherwise builds client-side from actualPathData.
   */
  const handleDownloadMarkdown = async () => {
    if (!learningPath) return;

    try {
      showNotification('Preparing Markdown...', 'info');

      // Prefer server export when we have a persisted entry
      if (entryId) {
        const mdBlob = await downloadLearningPathMarkdown(entryId);
        const url = URL.createObjectURL(mdBlob);
        const a = document.createElement('a');
        a.href = url;
        const fileName = learningPath.topic
          ? `course_${learningPath.topic.replace(/\s+/g, '_').substring(0, 30)}.md`
          : 'course.md';
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        showNotification('Markdown downloaded successfully', 'success');
        return;
      }

      // Fallback: build client-side Markdown from the in-memory data
      const md = buildClientMarkdown(learningPath);
      const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const fileName = learningPath.topic
        ? `course_${learningPath.topic.replace(/\s+/g, '_').substring(0, 30)}.md`
        : 'course.md';
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showNotification('Markdown downloaded successfully', 'success');
    } catch (err) {
      console.error('Error downloading Markdown:', err);
      showNotification('Failed to download Markdown', 'error');
    }
  };

  /**
   * Opens the selective export dialog
   */
  const handleSelectiveMarkdownExport = () => {
    if (!learningPath) {
      showNotification('No course data available for export', 'error');
      return;
    }
    setSelectiveExportDialogOpen(true);
  };

  /**
   * Handles the selective export with user choices
   */
  const handleSelectiveExport = async (filteredData, options) => {
    try {
      showNotification('Generating selective export...', 'info');

      // Build the selective markdown
      const markdownContent = buildSelectiveMarkdown(filteredData, {
        ...options,
        language: learningPath?.language || 'es'
      });

      // Create filename
      const filename = createSelectiveFilename(
        learningPath.topic || 'course',
        options.selectionStats,
        learningPath?.language || 'es'
      );

      // Create and download the file
      const blob = new Blob([markdownContent], { type: 'text/markdown;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      const { selectedModules, selectedSubmodules } = options.selectionStats;
      showNotification(
        `Selective export completed: ${selectedModules} modules, ${selectedSubmodules} submodules`,
        'success'
      );

      setSelectiveExportDialogOpen(false);
    } catch (error) {
      console.error('Error in selective export:', error);
      showNotification('Failed to generate selective export', 'error');
    }
  };

  /**
   * Closes the selective export dialog
   */
  const handleSelectiveExportClose = () => {
    setSelectiveExportDialogOpen(false);
  };

  // Lightweight client-side Markdown assembler mirroring backend structure
  const buildClientMarkdown = (lp) => {
    const topic = lp?.topic || 'Untitled Course';
    const creationDate = (lp?.creation_date) ? new Date(lp.creation_date) : null;
    const lastModified = (lp?.last_modified_date) ? new Date(lp.last_modified_date) : null;
    const tags = lp?.tags || [];
    const source = lp?.source || 'generated';

    const fmt = (d) => (d && !isNaN(d.getTime())) ? d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

    const preprocess = (text) => {
      if (!text) return '';
      let t = String(text);
      if (t.startsWith('```markdown\n')) t = t.replace(/^```markdown\n/, '');
      t = t.replace(/(^|\n)(\#{1,6})([^\s#])/g, '$1$2 $3');
      return t;
    };

    const getModules = () => {
      const pd = lp?.path_data || {};
      let modules = Array.isArray(pd.modules) ? pd.modules : [];
      if (!modules.length && pd.content && Array.isArray(pd.content.modules)) {
        modules = pd.content.modules;
      }
      if (!modules.length) {
        const firstList = Object.values(pd).find(v => Array.isArray(v) && v.every(it => typeof it === 'object'));
        modules = Array.isArray(firstList) ? firstList : [];
      }
      return modules;
    };

    const lines = [];
    lines.push(`# ${topic}`);
    lines.push('');
    lines.push(`- Created: ${fmt(creationDate)}`);
    if (lastModified) lines.push(`- Last Modified: ${fmt(lastModified)}`);
    if (tags.length) lines.push(`- Tags: ${tags.join(', ')}`);
    lines.push(`- Source: ${source}`);
    lines.push('');

    const modules = getModules();
    if (modules.length) {
      lines.push('## Table of Contents');
      modules.forEach((m, i) => {
        const mt = m?.title || `Module ${i + 1}`;
        lines.push(`- ${i + 1}. ${mt}`);
        const sub = m?.submodules || m?.sub_modules || m?.subModules || m?.subjects || m?.topics || m?.subtopics || m?.lessons || [];
        if (Array.isArray(sub) && sub.length) {
          sub.forEach((s, j) => lines.push(`  - ${i + 1}.${j + 1} ${s?.title || `Subtopic ${j + 1}`}`));
        }
      });
      lines.push('');
    }

    modules.forEach((m, i) => {
      const mt = m?.title || `Module ${i + 1}`;
      lines.push(`## ${mt}`);
      lines.push('');
      const mdesc = preprocess(m?.description || '');
      if (mdesc) {
        lines.push(mdesc.trim());
        lines.push('');
      }
      const mres = Array.isArray(m?.resources) ? m.resources : [];
      if (mres.length) {
        lines.push('### Resources');
        mres.forEach(r => {
          const title = r?.title || 'Untitled';
          const url = r?.url;
          const t = r?.type;
          const d = r?.description;
          let bullet = url ? `- [${title}](${url})` : `- ${title}`;
          const parts = [];
          if (t) parts.push(t);
          if (d) parts.push(d);
          if (parts.length) bullet += ` — ${parts.join(' | ')}`;
          lines.push(bullet);
        });
        lines.push('');
      }
      const sub = m?.submodules || m?.sub_modules || m?.subModules || m?.subjects || m?.topics || m?.subtopics || m?.lessons || [];
      if (Array.isArray(sub)) {
        sub.forEach((s, j) => {
          const st = s?.title || `Subtopic ${j + 1}`;
          lines.push(`### ${st}`);
          lines.push('');
          const sdesc = preprocess(s?.description || '');
          const scontent = preprocess(s?.content || '');
          if (sdesc) {
            lines.push(sdesc.trim());
            lines.push('');
          }
          if (scontent) {
            lines.push(scontent.trim());
            lines.push('');
          }
          const sres = Array.isArray(s?.resources) ? s.resources : [];
          if (sres.length) {
            lines.push('### Resources');
            sres.forEach(r => {
              const title = r?.title || 'Untitled';
              const url = r?.url;
              const t = r?.type;
              const d = r?.description;
              let bullet = url ? `- [${title}](${url})` : `- ${title}`;
              const parts = [];
              if (t) parts.push(t);
              if (d) parts.push(d);
              if (parts.length) bullet += ` — ${parts.join(' | ')}`;
              lines.push(bullet);
            });
            lines.push('');
          }
        });
      }
    });

    lines.push(`\n---\nGenerated on ${new Date().toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })}`);

    return lines.join('\n').trim() + '\n';
  };

  /**
   * Navigates to home page
   */
  const handleHomeClick = () => {
    navigate('/');
  };

  /**
   * Navigates to generator page to create a new course
   */
  const handleNewLearningPathClick = () => {
    navigate('/generator');
  };
  
  /**
   * Opens the save dialog
   */
  const handleSaveToHistory = () => {
    if (detailsHaveBeenSet) {
      showNotification('Learning path details already set.', 'info');
      return;
    }
    // Reset dialog state
    setTags([]);
    setNewTag('');
    setFavorite(false);
    setSaveDialogOpen(true);
  };
  
  /**
   * Closes the save dialog
   */
  const handleSaveDialogClose = () => {
    setSaveDialogOpen(false);
  };
  
  /**
   * Saves the course to history
   */
  const handleSaveConfirm = async () => {
    if (!learningPath) {
      showNotification('Learning path data is not available to save.', 'error');
      return null;
    }
    
    if (detailsHaveBeenSet) {
       showNotification('Learning path details already set.', 'info');
       return null; // Or return indicating already saved
    }

    try {
      showNotification('Saving details...', 'info');
      let response;
      let successEntryId = entryId; // Assume existing entryId for updates

      if (isFromHistory) {
        // --- Update existing history entry --- 
        console.log(`Updating history entry ${entryId} with details...`);
        const updatePayload = { 
          favorite: favorite, 
          tags: tags 
        };
        response = await updateHistoryEntry(entryId, updatePayload);
        // Assuming updateHistoryEntry returns success confirmation, maybe { success: true }
        // If it returns the updated entry, adjust accordingly.
      } else {
        // --- Save new entry to history --- 
        console.log('Saving new entry to history...');
        const payload = {
          path_data: learningPath,        
          topic: learningPath.topic || 'Untitled Course', 
          favorite: favorite,             
          tags: tags,                     
          source_task_id: taskId,         
        };
        if (temporaryPathId) { 
           payload.temporary_path_id = temporaryPathId;
           console.log('Saving path with temporary_path_id:', temporaryPathId);
        }
        response = await saveToHistory(learningPath, 'generated', taskId, payload); // Pass full payload now
        // Keep original logic: saveToHistory returns { path_id: new_id }
        if (response && response.path_id) {
           successEntryId = response.path_id; // Update entryId if new one was created
        }
      }
      
      // Handle response - update state, show success/error
      // Simplify response check: Check if response indicates success (might need adjustment based on actual API response)
      if (response) { // Basic check, refine if API gives clearer success/error
        showNotification('Learning path details saved successfully!', 'success');
        setSaveDialogOpen(false);
        
        // Invoke the callback passed from the parent component with the relevant entryId
        if (onSaveSuccess) {
          onSaveSuccess({ entryId: successEntryId });
        }

        // Return success and the relevant entry ID
        return { success: true, entryId: successEntryId }; 
      } else {
         // Throw an error if the response structure wasn't as expected
         throw new Error('API response did not indicate success.');
      }

    } catch (error) {
      console.error("Error saving course:", error);
      showNotification(`Error saving course: ${error.message || 'Unknown error'}`, 'error');
      setSaveDialogOpen(false); // Close dialog on error too
      return null;
    }
  };

  const handleSaveOffline = async () => {
    if (!learningPath) {
      showNotification('Learning path data is not available.', 'error');
      return;
    }
    try {
      showNotification('Saving for offline use...', 'info');
      const id = await saveOfflinePath(learningPath);
      if (id) {
        showNotification('Saved for offline use', 'success');
      } else {
        showNotification('Failed to save offline. Please free up storage and try again.', 'error');
      }
    } catch (e) {
      console.error('Offline save error:', e);
      showNotification('Failed to save offline. Please free up storage and try again.', 'error');
    }
  };
  
  // Tag management functions
  const handleAddTag = () => {
    if (newTag.trim() && !tags.includes(newTag.trim())) {
      setTags([...tags, newTag.trim()]);
      setNewTag('');
    }
  };
  
  const handleDeleteTag = (tagToDelete) => {
    setTags(tags.filter(tag => tag !== tagToDelete));
  };
  
  const handleTagKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddTag();
    }
  };

  return {
    // States
    saveDialogOpen,
    setSaveDialogOpen,
    selectiveExportDialogOpen,
    tags,
    setTags,
    newTag,
    setNewTag,
    favorite,
    setFavorite,
    notification,
    
    // Actions
    handleDownloadJSON,
    handleDownloadPDF,
    handleDownloadMarkdown,
    handleSelectiveMarkdownExport,
    handleSelectiveExport,
    handleSelectiveExportClose,
    handleHomeClick,
    handleNewLearningPathClick,
    handleSaveToHistory,
    handleSaveDialogClose,
    handleSaveConfirm,
    handleSaveOffline,
    handleAddTag,
    handleDeleteTag,
    handleTagKeyDown,
    handleNotificationClose,
    showNotification
  };
};

export default useLearningPathActions; 