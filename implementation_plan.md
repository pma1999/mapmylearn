# Implementation Plan

[Overview]
Actualizar la renderización de descripciones de módulos y submódulos para soportar Markdown completo (énfasis, listas, enlaces, código) con sanitización robusta en ContentPanel, CourseOverview y ModuleNavigationColumn.

El objetivo es que todas las descripciones visibles en la UI (encabezados de submódulos, descripciones de módulos y texto secundario en listados) se muestren usando un renderer Markdown consistente y seguro. Reutilizaremos el componente existente `MarkdownRenderer` que ya incorpora remark-gfm y saneamiento, y añadiremos un pequeño wrapper `MarkdownInline` para controlar variantes tipográficas (variant/color/sx) y desactivar generación de IDs en textos cortos. Las modificaciones serán mínimas y localizadas para evitar romper otras funcionalidades (TOC, generación de ids, y resaltado de código). Se documentarán cambios y se añadirá cobertura de pruebas (unitarias y de snapshot/visual) y pasos de validación manual.

[Types]  
No se introducen cambios de TypeScript; se definen PropTypes y contratos claros para los nuevos wrappers/componentes.

- MarkdownInline (props):
  - children: PropTypes.node.isRequired — contenido Markdown (string o React node).
  - variant: PropTypes.string (default: 'body2') — MUI typography variant a aplicar visualmente.
  - color: PropTypes.string — color CSS o token de MUI para el texto.
  - enableTocIds: PropTypes.bool (default: false) — si true, permite generar ids para headers (no recomendado en descripciones pequeñas).
  - headerIdMap: PropTypes.instanceOf(Map) (opcional) — si se desea mapear ids del TOC.
  - sx: PropTypes.object (opcional) — estilos MUI sx aplicados al wrapper.
  - className: PropTypes.string (opcional) — para pruebas o overrides.

Validaciones:
- children -> si es null/undefined se renderiza null (o un Box vacío según el contexto).
- variant debe ser un variant válido de MUI; si no, fallback a 'body2'.
- enableTocIds por defecto false para evitar colisiones de ids en lugares repetidos.

[Files]
Single sentence describing file modifications.
Se crearán y modificarán archivos en frontend con rutas y cambios concretos listados a continuación.

- Nuevos archivos a crear:
  - frontend/src/components/MarkdownInline.jsx
    - Propósito: wrapper compacto que aplica `MarkdownRenderer` y envuelve el resultado en un Box/ Typography con soporte `variant`, `color` y `sx`. Evita generar ids de TOC por defecto.
    - Contenido: componente React con PropTypes documentadas.

- Archivos existentes a modificar:
  - frontend/src/components/learning-path/view/ContentPanel.jsx
    - Cambios:
      - Importar `MarkdownInline` (o `MarkdownRenderer` directamente).
      - Reemplazar renderizado de `submodule.description` en la cabecera del panel por:
         <MarkdownInline variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }} enableTocIds={false}>
           {submodule.description}
         </MarkdownInline>
      - Reemplazar `module.description` en la vista `module_resources` por equivalente `MarkdownInline`.
      - Asegurar que, si description es null/empty, no renderice elemento vacío o renderice fallback (null).
  - frontend/src/components/learning-path/view/CourseOverview.jsx
    - Cambios:
      - Importar `MarkdownInline`.
      - Reemplazar `<Typography variant="body2" color="text.secondary">{module.description}</Typography>` por `<MarkdownInline variant="body2" color="text.secondary">{module.description}</MarkdownInline>`.
      - Reemplazar `ListItemText secondary={submodule.description}` por `secondary={<MarkdownInline variant="caption" color="text.secondary">{submodule.description}</MarkdownInline>}` (asegurando que el componente acepta nodo React en `secondary`).
  - frontend/src/components/learning-path/view/ModuleNavigationColumn.jsx
    - Cambios:
      - Importar `MarkdownInline`.
      - Reemplazar `Typography` que muestra `module.description` por `<MarkdownInline variant="body2" color="text.secondary">{module.description}</MarkdownInline>`.
      - Revisar si se deben aplicar límites de longitud (opcional): mostrar solo primera línea en nav si texto excesivamente largo; añadir CSS `overflow: hidden` y `textOverflow: ellipsis` si procede.
- Archivos a auditar (sin cambios planificados):
  - frontend/src/components/MarkdownRenderer.js — se reutiliza tal cual; verificar export y props.
  - frontend/src/components/learning-path/hooks/useMarkdownTOC.js — sigue usando parseMarkdownHeaders/generateHeaderId.
  - frontend/src/components/learning-path/utils/markdownParser.js — sin cambios.
  - frontend/src/components/learning-path/components/SubmoduleTableOfContents.jsx — verificar compatibilidad si se genera id en lugares nuevos.

- Archivos a eliminar o mover: ninguno.

- Configuración:
  - No se requieren cambios en package.json. Recomendación opcional: si se desea mayor seguridad, añadir rehype-sanitize (rehype-sanitize + rehype-raw) y ajustar `ReactMarkdown` configuración, pero esto es opcional ya que existe `sanitizeContent` utilitario.

[Functions]
Single sentence describing function modifications.
Se introducirán un nuevo componente funcional `MarkdownInline` y se actualizarán render functions en componentes de vista para delegar a `MarkdownRenderer`.

- Nuevas funciones / componentes:
  - MarkdownInline (functional component)
    - Nombre: MarkdownInline
    - Ruta: frontend/src/components/MarkdownInline.jsx
    - Firma: ({ children, variant = 'body2', color = 'text.secondary', enableTocIds = false, headerIdMap = null, sx = {}, className }) => JSX.Element
    - Propósito: aplicar `MarkdownRenderer` a `children`, envolver en MUI Box/typography y exponer props de estilo.
    - Implementación clave:
      - Si `!children` -> return null.
      - Render:
        <Box component="div" sx={{ ...sx }} className={className}>
          <Typography component="div" variant={variant} color={color} sx={{ display: 'block' }}>
            <MarkdownRenderer enableTocIds={enableTocIds} headerIdMap={headerIdMap}>
              {children}
            </MarkdownRenderer>
          </Typography>
        </Box>
      - Nota: usar `component="div"` en Typography para evitar etiquetas semánticas no deseadas (p dentro de p).

- Funciones modificadas:
  - ContentPanel (component)
    - Archivo: frontend/src/components/learning-path/view/ContentPanel.jsx
    - Cambios exactos:
      - Reemplazar los 2-3 lugares donde `submodule.description` o `module.description` se renderiza con `Typography` por `MarkdownInline` (ver [Files] para ubicaciones).
      - Asegurar `enableTocIds={false}` para evitar ids en descripciones cortas.
  - CourseOverview (component)
    - Archivo: frontend/src/components/learning-path/view/CourseOverview.jsx
    - Cambios:
      - Reemplazar `Typography` y `ListItemText secondary` que muestran descripciones por `MarkdownInline`.
      - En `ListItemText` el prop `secondary` puede aceptar nodo React; utilizar `<MarkdownInline variant="caption">`.
  - ModuleNavigationColumn (component)
    - Archivo: frontend/src/components/learning-path/view/ModuleNavigationColumn.jsx
    - Cambios:
      - Reemplazar `Typography` con `MarkdownInline`.
      - Aplicar `sx` para truncado si es necesario.

- Funciones removidas:
  - Ninguna.

[Classes]
Single sentence describing class modifications.
No clases ES6/React class components se añaden ni se eliminan; el trabajo se basa en componentes funcionales.

- Nuevas clases: ninguna (solo componentes funcionales).
- Modificaciones a clases existentes: ninguna.
- Eliminaciones de clases: ninguna.

[Dependencies]
Single sentence describing dependency modifications.
No dependencias nuevas obligatorias; opción optativa para rehype-sanitize se documenta para mayor seguridad.

- Recomendaciones:
  - Ninguna dependencia obligatoria nueva.
  - Opcional: instalar `rehype-sanitize` y `rehype-raw` si se decide mejorar la sanitización a nivel de rehype:
    - npm install rehype-sanitize rehype-raw
    - Ajustes en MarkdownRenderer: usar rehypePlugins={[rehypeRaw, [rehypeSanitize, schema]]} y ajustar skipHtml.
  - Si se desea mejorar coherencia de estilos de código, asegurar `react-syntax-highlighter` está en dependencies (ya está siendo importado de manera dinámica; auditar package.json solo por si faltara).

[Testing]
Single sentence describing testing approach.
Agregar pruebas unitarias y manuales: snapshots para renderizado Markdown en los tres componentes y pruebas end-to-end/manual para verificar cursiva, listas, enlaces y código, además de pruebas de seguridad (XSS sanitization).

- Test files to add/modify:
  - frontend/test/markdown/MarkdownInline.test.jsx
    - Tests:
      - Render simple inline emphasis: "*italica*" => <em> rendered.
      - Render bold, links, inline code, fenced code block.
      - Ensure empty children returns null.
  - frontend/test/components/ContentPanel.markdown.snap.jsx (snapshot)
    - Snapshot with a sample `submodule.description` containing emphasis and list.
  - frontend/test/components/CourseOverview.markdown.snap.jsx
    - Snapshot verifying `module.description` and submodule `secondary` rendering with markdown.
  - frontend/test/components/ModuleNavigationColumn.markdown.snap.jsx
    - Snapshot verifying module description rendering.
- Integration/manual tests:
  - Run local dev server, open a course with descriptions containing `*italica*`, `_italic_`, `**bold**`, lists and code blocks, ensure correct rendering in:
    - ContentPanel (submodule view)
    - CourseOverview (module card & submodule list secondary)
    - ModuleNavigationColumn (module expanded view)
  - Verify that generated TOC and header ids are unchanged for actual headers inside `submodule.content`, not for short descriptions (enableTocIds=false).
  - Security test: try a description containing `<script>alert(1)</script>` and `onerror` handlers in images — ensure nothing executes and script tags are removed.
- CI:
  - Add tests to test suite; run `npm test` or existing test harness to include new tests.

[Implementation Order]
Single sentence describing the implementation sequence.
Aplicar cambios en pequeñas etapas: añadir wrapper, actualizar tres componentes (ContentPanel, CourseOverview, ModuleNavigationColumn), añadir pruebas y realizar validaciones manuales; desplegar después de revisión.

Paso a paso:
1. Crear `frontend/src/components/MarkdownInline.jsx` (componente y PropTypes) — commit separado.
2. Ejecutar tests unitarios básicos (si existen) y añadir tests para MarkdownInline.
3. Modificar `ContentPanel.jsx`:
   - Importar `MarkdownInline`.
   - Reemplazar `submodule.description` y `module.description` en las ubicaciones indicadas.
   - Ejecutar tests/snapshots.
4. Modificar `CourseOverview.jsx`:
   - Importar `MarkdownInline`.
   - Reemplazar `Typography` y `ListItemText secondary` con `MarkdownInline`.
   - Actualizar/crear snapshots de componente.
5. Modificar `ModuleNavigationColumn.jsx`:
   - Importar `MarkdownInline` y reemplazar `module.description`.
   - Añadir CSS `sx` para truncado (opcional).
6. Ejecutar cobertura manual y pruebas de XSS/sanitización.
7. Revisar UI en servidor de desarrollo (npm start), verificar casos edge: null descriptions, muy largas, markdown mixto con HTML.
8. Commit final y PR con descripción detallada del cambio y checklist de pruebas manuales realizadas.
