/**
 * Enhanced Markdown builder for selective export
 * Supports filtering content based on user selection and includes professional formatting
 */

/**
 * Builds a selective Markdown document based on user selections
 * @param {Object} pathData - The course path data
 * @param {Object} options - Export options
 * @param {boolean} options.includeMetadata - Include course metadata
 * @param {boolean} options.includeTableOfContents - Include table of contents
 * @param {boolean} options.includeResources - Include resources
 * @param {Object} options.selectedItems - Selected items mapping
 * @param {Object} options.selectionStats - Selection statistics
 * @param {string} options.language - Language for text labels
 * @returns {string} Formatted Markdown content
 */
export const buildSelectiveMarkdown = (pathData, options = {}) => {
  const {
    includeMetadata = true,
    includeTableOfContents = true,
    includeResources = true,
    selectedItems = {},
    selectionStats = {},
    language = 'es'
  } = options;

  // Language-specific texts
  const texts = {
    es: {
      createdOn: 'Creado el',
      lastModified: 'Última modificación',
      tags: 'Etiquetas',
      source: 'Fuente',
      tableOfContents: 'Índice de Contenidos',
      resources: 'Recursos',
      moduleResources: 'Recursos del Módulo',
      generatedOn: 'Generado el',
      exportedContent: 'Contenido Exportado',
      modules: 'módulos',
      submodules: 'submódulos',
      resourcesCount: 'recursos',
      selectiveExport: 'Exportación Selectiva'
    },
    en: {
      createdOn: 'Created on',
      lastModified: 'Last modified',
      tags: 'Tags',
      source: 'Source',
      tableOfContents: 'Table of Contents',
      resources: 'Resources',
      moduleResources: 'Module Resources',
      generatedOn: 'Generated on',
      exportedContent: 'Exported Content',
      modules: 'modules',
      submodules: 'submodules',
      resourcesCount: 'resources',
      selectiveExport: 'Selective Export'
    }
  };

  const t = texts[language] || texts.en;
  
  const topic = pathData?.topic || 'Untitled Course';
  const creationDate = pathData?.creation_date ? new Date(pathData.creation_date) : null;
  const lastModified = pathData?.last_modified_date ? new Date(pathData.last_modified_date) : null;
  const tags = pathData?.tags || [];
  const source = pathData?.source || 'generated';
  const modules = pathData?.modules || [];

  const lines = [];
  
  // Helper function to format dates
  const formatDate = (date) => {
    if (!date || isNaN(date.getTime())) return 'N/A';
    return date.toLocaleDateString(undefined, { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    });
  };

  // Helper function to preprocess text content
  const preprocessText = (text) => {
    if (!text) return '';
    let processedText = String(text);
    
    // Remove markdown wrapper if present
    if (processedText.startsWith('```markdown\n')) {
      processedText = processedText.replace(/^```markdown\n/, '');
    }
    
    // Ensure proper spacing after headers
    processedText = processedText.replace(/(^|\n)(\#{1,6})([^\s#])/g, '$1$2 $3');
    
    return processedText.trim();
  };

  // Helper function to create safe filename-compatible strings
  const sanitizeString = (str) => {
    return str.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_');
  };

  // 1. Document Header
  lines.push(`# ${topic}`);
  lines.push('');

  // 2. Selective Export Notice
  if (selectionStats.selectedModules !== undefined) {
    lines.push(`> **${t.selectiveExport}**: ${t.exportedContent} - ${selectionStats.selectedModules} ${t.modules}, ${selectionStats.selectedSubmodules} ${t.submodules}${selectionStats.selectedResources > 0 ? `, ${selectionStats.selectedResources} ${t.resourcesCount}` : ''}`);
    lines.push('');
  }

  // 3. Metadata Section
  if (includeMetadata) {
    if (creationDate) {
      lines.push(`- **${t.createdOn}**: ${formatDate(creationDate)}`);
    }
    if (lastModified) {
      lines.push(`- **${t.lastModified}**: ${formatDate(lastModified)}`);
    }
    if (tags.length > 0) {
      lines.push(`- **${t.tags}**: ${tags.join(', ')}`);
    }
    lines.push(`- **${t.source}**: ${source}`);
    lines.push('');
  }

  // 4. Table of Contents
  if (includeTableOfContents && modules.length > 0) {
    lines.push(`## ${t.tableOfContents}`);
    lines.push('');
    
    let displayModuleNumber = 1;
    modules.forEach((module, moduleIndex) => {
      // Use original module index from metadata if available, otherwise use current index
      const originalModuleIndex = module?.originalIndex !== undefined ? module.originalIndex : moduleIndex;
      const moduleKey = `module_${originalModuleIndex}`;
      if (!selectedItems[moduleKey]) return;

      // Use original module number (1-based) for display
      const originalModuleNumber = originalModuleIndex + 1;
      const baseTitle = module?.title || `Módulo ${originalModuleNumber}`;
      const moduleTitle = module?.title ? `Módulo ${originalModuleNumber}: ${baseTitle}` : `Módulo ${originalModuleNumber}`;
      lines.push(`${displayModuleNumber}. [${moduleTitle}](#${sanitizeString(moduleTitle).toLowerCase()})`);
      
      // Add submodules to TOC
      const submodules = module?.submodules || [];
      let displaySubmoduleNumber = 1;
      submodules.forEach((submodule, submoduleIndex) => {
        const submoduleKey = `module_${originalModuleIndex}_sub_${submoduleIndex}`;
        if (selectedItems[submoduleKey]) {
          const originalSubmoduleNumber = submoduleIndex + 1;
          const baseSubTitle = submodule?.title || `Submódulo ${originalSubmoduleNumber}`;
          const submoduleTitle = submodule?.title ? `${originalModuleNumber}.${originalSubmoduleNumber} ${baseSubTitle}` : `${originalModuleNumber}.${originalSubmoduleNumber} Submódulo ${originalSubmoduleNumber}`;
          lines.push(`   ${displayModuleNumber}.${displaySubmoduleNumber}. [${submoduleTitle}](#${sanitizeString(submoduleTitle).toLowerCase()})`);
          displaySubmoduleNumber++;
        }
      });
      displayModuleNumber++;
    });
    lines.push('');
  }

  // 5. Module Content
  let displayModuleNumber = 1;
  modules.forEach((module, moduleIndex) => {
    // Use original module index from metadata if available, otherwise use current index
    const originalModuleIndex = module?.originalIndex !== undefined ? module.originalIndex : moduleIndex;
    const moduleKey = `module_${originalModuleIndex}`;
    if (!selectedItems[moduleKey]) return;

    // Use original module number (1-based) for display
    const originalModuleNumber = originalModuleIndex + 1;
    const baseTitle = module?.title || `Módulo ${originalModuleNumber}`;
    const moduleTitle = module?.title ? `Módulo ${originalModuleNumber}: ${baseTitle}` : `Módulo ${originalModuleNumber}`;
    
    // Module Header
    lines.push(`## ${moduleTitle}`);
    lines.push('');
    
    // Module Description
    const moduleDescription = preprocessText(module?.description || '');
    if (moduleDescription) {
      lines.push(moduleDescription);
      lines.push('');
    }

    // Module Resources
    if (includeResources && selectedItems[`${moduleKey}_resources`] && module.resources && module.resources.length > 0) {
      lines.push(`### ${t.moduleResources}`);
      lines.push('');
      
      module.resources.forEach(resource => {
        const title = resource?.title || 'Untitled Resource';
        const url = resource?.url;
        const type = resource?.type;
        const description = resource?.description;
        
        let resourceLine = url ? `- [${title}](${url})` : `- ${title}`;
        
        const details = [];
        if (type) details.push(type);
        if (description) details.push(description);
        if (details.length > 0) {
          resourceLine += ` — ${details.join(' | ')}`;
        }
        
        lines.push(resourceLine);
      });
      lines.push('');
    }

    // Submodules
    const submodules = module?.submodules || [];
    let displaySubmoduleNumber = 1;
    submodules.forEach((submodule, submoduleIndex) => {
      const submoduleKey = `module_${originalModuleIndex}_sub_${submoduleIndex}`;
      if (!selectedItems[submoduleKey]) return;

      // Use original submodule number (1-based) for display
      const originalSubmoduleNumber = submoduleIndex + 1;
      const baseSubTitle = submodule?.title || `Submódulo ${originalSubmoduleNumber}`;
      const submoduleTitle = submodule?.title ? `${originalModuleNumber}.${originalSubmoduleNumber} ${baseSubTitle}` : `${originalModuleNumber}.${originalSubmoduleNumber} Submódulo ${originalSubmoduleNumber}`;
      
      // Submodule Header
      lines.push(`### ${submoduleTitle}`);
      lines.push('');
      
      // Submodule Description
      const submoduleDescription = preprocessText(submodule?.description || '');
      if (submoduleDescription) {
        lines.push(submoduleDescription);
        lines.push('');
      }
      
      // Submodule Content
      const submoduleContent = preprocessText(submodule?.content || '');
      if (submoduleContent) {
        lines.push(submoduleContent);
        lines.push('');
      }
      
      // Submodule Resources
      if (includeResources && submodule.resources && submodule.resources.length > 0) {
        lines.push(`#### ${t.resources}`);
        lines.push('');
        
        submodule.resources.forEach(resource => {
          const title = resource?.title || 'Untitled Resource';
          const url = resource?.url;
          const type = resource?.type;
          const description = resource?.description;
          
          let resourceLine = url ? `- [${title}](${url})` : `- ${title}`;
          
          const details = [];
          if (type) details.push(type);
          if (description) details.push(description);
          if (details.length > 0) {
            resourceLine += ` — ${details.join(' | ')}`;
          }
          
          lines.push(resourceLine);
        });
        lines.push('');
      }
      displaySubmoduleNumber++;
    });
    displayModuleNumber++;
  });

  // 6. Footer
  lines.push('---');
  lines.push(`*${t.generatedOn} ${formatDate(new Date())}*`);

  // Join all lines and ensure proper formatting
  return lines.join('\n').replace(/\n{3,}/g, '\n\n') + '\n';
};

/**
 * Creates a filename for the selective export
 * @param {string} topic - Course topic
 * @param {Object} selectionStats - Selection statistics
 * @param {string} language - Language for filename
 * @returns {string} Safe filename
 */
export const createSelectiveFilename = (topic, selectionStats = {}, language = 'es') => {
  const baseTitle = topic || 'course';
  const sanitizedTitle = baseTitle.replace(/[^\w\s-]/g, '').replace(/\s+/g, '_').substring(0, 30);
  
  const suffix = language === 'es' ? 'selectivo' : 'selective';
  
  if (selectionStats.selectedModules !== undefined) {
    const statsString = `${selectionStats.selectedModules}m_${selectionStats.selectedSubmodules}s`;
    return `${sanitizedTitle}_${suffix}_${statsString}.md`;
  }
  
  return `${sanitizedTitle}_${suffix}.md`;
};

/**
 * Validates selection before export
 * @param {Object} selectedItems - Selected items mapping
 * @param {Array} modules - Course modules
 * @returns {Object} Validation result
 */
export const validateSelection = (selectedItems, modules) => {
  const hasSelectedModules = Object.keys(selectedItems).some(key => 
    key.startsWith('module_') && !key.includes('sub_') && !key.includes('resources') && selectedItems[key]
  );

  const hasSelectedSubmodules = Object.keys(selectedItems).some(key => 
    key.includes('sub_') && selectedItems[key]
  );

  const selectedModuleCount = modules.filter((module, index) => {
    const originalIndex = module?.originalIndex !== undefined ? module.originalIndex : index;
    return selectedItems[`module_${originalIndex}`];
  }).length;

  return {
    isValid: hasSelectedModules || hasSelectedSubmodules,
    hasContent: selectedModuleCount > 0,
    selectedModuleCount,
    isEmpty: !hasSelectedModules && !hasSelectedSubmodules
  };
};