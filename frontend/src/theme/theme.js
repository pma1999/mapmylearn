import { createTheme } from '@mui/material/styles';

// Define color palette
const palette = {
  primary: {
    main: '#136090', // Darker Logo Blue
    light: '#588fc7', // Estimated Light Blue
    dark: '#003762', // Estimated Dark Blue
    contrastText: '#ffffff',
  },
  secondary: {
    main: '#52b8cc', // Lighter Logo Teal
    light: '#86eaff', // Estimated Light Teal
    dark: '#00889b', // Estimated Dark Teal
    contrastText: '#042645', // Dark text for contrast on light teal
  },
  error: {
    main: '#D32F2F', // Standard Red
  },
  warning: {
    main: '#ED6C02', // Standard Orange
  },
  info: {
    main: '#136090', // Using Primary Blue
  },
  success: {
    main: '#2E7D32', // Standard Green
  },
  background: {
    default: '#F2F2F7', // Slightly off-white
    paper: '#FFFFFF',
  },
  text: {
    primary: '#042645', // Logo Text Navy
    secondary: '#5A6D7C', // Estimated Medium Gray/Blue
    disabled: '#AEB7C0', // Estimated Light Gray
  },
  divider: '#E5E5EA', // Light Gray Divider
  action: {
    active: 'rgba(4, 38, 69, 0.54)', // Derived from text.primary
    hover: 'rgba(4, 38, 69, 0.04)',  // Derived from text.primary
    selected: 'rgba(19, 96, 144, 0.08)', // Derived from primary.main
    disabled: 'rgba(4, 38, 69, 0.26)', // Derived from text.primary
    disabledBackground: 'rgba(4, 38, 69, 0.12)', // Derived from text.primary
    focus: 'rgba(4, 38, 69, 0.12)' // Derived from text.primary
  }
};

// Define typography settings
const typography = {
  fontFamily: '\'Inter\', -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, \'Helvetica Neue\', Arial, sans-serif, \'Apple Color Emoji\', \'Segoe UI Emoji\', \'Segoe UI Symbol\'',
  fontWeightLight: 300,
  fontWeightRegular: 400,
  fontWeightMedium: 500,
  fontWeightBold: 700,
  h1: {
    fontSize: '2.5rem', // 40px
    fontWeight: 700,
    lineHeight: 1.2,
  },
  h2: {
    fontSize: '2rem', // 32px
    fontWeight: 700,
    lineHeight: 1.25,
  },
  h3: {
    fontSize: '1.75rem', // 28px
    fontWeight: 600,
    lineHeight: 1.3,
  },
  h4: {
    fontSize: '1.5rem', // 24px
    fontWeight: 600,
    lineHeight: 1.35,
  },
  h5: {
    fontSize: '1.25rem', // 20px
    fontWeight: 600,
    lineHeight: 1.4,
  },
  h6: {
    fontSize: '1.125rem', // 18px
    fontWeight: 600,
    lineHeight: 1.45,
  },
  subtitle1: {
    fontSize: '1rem', // 16px
    fontWeight: 500,
    lineHeight: 1.5,
  },
  subtitle2: {
    fontSize: '0.875rem', // 14px
    fontWeight: 500,
    lineHeight: 1.5,
  },
  body1: {
    fontSize: '1rem', // 16px
    fontWeight: 400,
    lineHeight: 1.6, // Increased for readability
  },
  body2: {
    fontSize: '0.875rem', // 14px
    fontWeight: 400,
    lineHeight: 1.5,
  },
  button: {
    fontSize: '0.875rem', // 14px
    fontWeight: 600,
    textTransform: 'none', // Common modern practice
    lineHeight: 1.75,
  },
  caption: {
    fontSize: '0.75rem', // 12px
    fontWeight: 400,
    lineHeight: 1.66,
  },
  overline: {
    fontSize: '0.625rem', // 10px
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '1px',
    lineHeight: 2.5,
  },
};

// Create the theme instance
const theme = createTheme({
  palette: palette,
  typography: typography,
  shape: {
    borderRadius: 8, // Slightly more rounded corners
  },
  components: {
    // Base component overrides
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: palette.background.default,
          color: palette.text.primary,
        },
        '*': {
          boxSizing: 'border-box',
        },
        '#root': {
          minHeight: '100vh',
          display: 'flex', // Ensure root takes full height for flex layouts
          flexDirection: 'column', // Ensure root takes full height for flex layouts
        },
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
        variant: 'contained', // Make contained the default
      },
      styleOverrides: {
        root: {
          borderRadius: '6px', // Consistent with shape.borderRadius or slightly less
          padding: '8px 16px', // Adjust padding for better feel
        },
        containedPrimary: {
          '&:hover': {
            backgroundColor: palette.primary.dark,
          },
        },
        outlinedPrimary: {
          borderColor: palette.primary.main,
          '&:hover': {
            backgroundColor: palette.action.hover, // Use theme action color
            borderColor: palette.primary.dark,
          },
        },
        textPrimary: {
           '&:hover': {
             backgroundColor: palette.action.hover,
           }
        }
      },
    },
    MuiPaper: {
      defaultProps: {
        elevation: 0, // Default to no shadow, use borders instead
      },
      styleOverrides: {
        root: {
          backgroundColor: palette.background.paper,
        },
        outlined: {
          borderColor: palette.divider, // Use theme divider color
          borderWidth: '1px',
        }
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0, // Flat app bar
        color: 'inherit'
      },
      styleOverrides: {
         root: {
            backgroundColor: palette.background.paper,
            borderBottom: `1px solid ${palette.divider}`,
         }
      }
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          fontSize: '0.8125rem', // 13px
        },
        outlined: {
          borderColor: palette.divider,
          color: palette.text.secondary,
          backgroundColor: 'transparent',
        },
        filled: {
           backgroundColor: palette.primary.main,
           color: palette.primary.contrastText,
           '&:hover': {
             backgroundColor: palette.primary.dark,
           }
        }
        // Add other variants as needed
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: 'none', // From typography, but enforce here too
          fontWeight: 500,
          fontSize: '0.9375rem', // 15px
          minHeight: '48px',
          padding: '12px 16px',
          '&.Mui-selected': {
            color: palette.primary.main,
            fontWeight: 600,
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        indicator: {
          backgroundColor: palette.primary.main,
          height: '3px',
          borderTopLeftRadius: '3px',
          borderTopRightRadius: '3px',
        },
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          borderRadius: '6px',
          '&.Mui-selected': {
            backgroundColor: palette.action.selected,
            color: palette.primary.main,
            fontWeight: 600, // Use weight for emphasis
            '&:hover': {
              backgroundColor: palette.action.selected, // Keep selected color on hover
            },
            // Ensure text color remains primary when selected
            '.MuiListItemText-primary': {
               color: palette.primary.main,
               fontWeight: 600,
            }
          },
          '&:hover': {
            backgroundColor: palette.action.hover,
          },
        },
      },
    },
    MuiTooltip: {
       styleOverrides: {
          tooltip: {
             backgroundColor: palette.text.primary,
             color: palette.background.paper,
             fontSize: '0.75rem', // 12px
             borderRadius: '4px',
             padding: '4px 8px',
          },
          arrow: {
             color: palette.text.primary,
          }
       }
    },
    MuiAlert: {
      styleOverrides: {
         root: {
            borderRadius: '6px',
            borderWidth: '1px',
            borderStyle: 'solid',
         },
         standardInfo: {
            borderColor: palette.info.main,
            backgroundColor: `${palette.info.main}66`, // Light blue background
            color: palette.info.dark || palette.info.main, // Ensure text is dark enough
            '.MuiAlert-icon': { color: palette.info.main }
         },
         standardSuccess: {
            borderColor: palette.success.main,
            backgroundColor: `${palette.success.main}66`,
            color: palette.success.dark || palette.success.main,
            '.MuiAlert-icon': { color: palette.success.main }
         },
         standardWarning: {
            borderColor: palette.warning.main,
            backgroundColor: `${palette.warning.main}66`,
            color: palette.warning.dark || palette.warning.main,
            '.MuiAlert-icon': { color: palette.warning.main }
         },
         standardError: {
            borderColor: palette.error.main,
            backgroundColor: `${palette.error.main}66`,
            color: palette.error.dark || palette.error.main,
            '.MuiAlert-icon': { color: palette.error.main }
         },
      }
    },
    // Add other component overrides as needed
  },
});

export default theme; 