export const helpTexts = {
  // Welcome Modal
  welcomeTitle: "Welcome to MapMyLearn! 👋",
  welcomeValueProp: "Generate personalized courses on any topic with the power of AI.",
  welcomeHowItWorks: "How it Works: 1. Enter Topic ➔ 2. AI Generates Course ➔ 3. Learn Interactively (Content, Quiz, Chat).",
  welcomeCredits: (credits) => `Get Started: You have ${credits} free ${credits === 1 ? 'credit' : 'credits'}. Use them to generate courses or audio features.`,
  welcomeGo: "Let's Go!",

  // HomePage
  homeWhyTitle: "Why Choose MapMyLearn?",
  homeWhyDesc: "Our AI-powered platform creates personalized learning experiences that adapt to your specific needs and goals, including structured modules, quizzes, AI chat, and optional audio summaries.",
  homeHowTitle: "How It Works",
  homeHowDesc: "Simply tell us what you want to learn, and our AI will craft a detailed course to guide your studies.", // Existing steps are fine.

  // GeneratorPage
  generatorSubtitle: "Enter any topic. Our AI will build a custom course with lessons, activities, and AI chat tailored to you.",
  generatorCostHint: "Requires 1 credit",

  // HistoryPage
  historyEmptyState: "Your saved courses appear here. Generate a new course and click 'Save to History' on the results page to keep track of your learning journey.",

  // LearningPathView
  lpFirstViewAlert: "Explore your new course! Dive into Modules and Submodules. Use the tabs inside submodules for content, quizzes, resources, and AI chat.",

  // Navbar
  navbarCreditsTooltip: "Credits are used for features like course generation (1 credit) and audio generation. Click to buy more.",
  navbarPurchaseMore: "Purchase more", // Link text if needed, might be separate button

  // LearningPathHeader
  lphSaveTooltip: "Save this course permanently to your History tab to access it later.",

  // SubmoduleCard Tabs
  submoduleTabQuiz: "Test your knowledge on this topic.",
  submoduleTabChat: "Ask the AI specific questions about this submodule's content.",
  submoduleTabAudio: (cost) => `Generate a spoken audio summary of this content (costs ${cost} credit).`,
  submoduleTabVisualization: (cost) => `Generate an interactive diagram of this submodule's content (costs ${cost} credit).`,

  // Enhanced PWA Tutorial System
  pwaIntro: {
    // Main titles and navigation
    title: "Get the Full MapMyLearn Experience",
    subtitle: "Install our app for the best learning experience",
    nextButton: "Continue",
    backButton: "Back", 
    skipButton: "Skip Tutorial",
    finishButton: "Get Started!",
    
    // Step 1: Value Proposition
    step1: {
      title: "Why Install MapMyLearn?",
      subtitle: "Transform your mobile device into a powerful learning companion",
      benefits: [
        {
          icon: "🚀",
          title: "Faster Access",
          description: "Launch instantly from your home screen without opening a browser"
        },
        {
          icon: "📱",
          title: "Native App Feel",
          description: "Full-screen experience optimized for mobile learning"
        },
        {
          icon: "📚",
          title: "Offline Learning",
          description: "Access your saved courses anywhere, even without internet"
        },
        {
          icon: "🔔",
          title: "Smart Notifications",
          description: "Get reminders to continue your learning journey"
        }
      ],
      callToAction: "Let's set it up in just 30 seconds!"
    },

    // Step 2: Installation Instructions (Browser-Specific)
    step2: {
      title: "Install MapMyLearn",
      subtitle: "Follow these simple steps for your browser",
      
      safari_ios: {
        title: "Install on iPhone/iPad (Safari)",
        steps: [
          {
            instruction: "Tap the Share button at the bottom of Safari",
            icon: "share",
            detail: "Look for the square with an arrow pointing up"
          },
          {
            instruction: "Scroll down and tap 'Add to Home Screen'",
            icon: "add_to_home_screen",
            detail: "You'll see the MapMyLearn icon preview"
          },
          {
            instruction: "Tap 'Add' to complete installation",
            icon: "check_circle",
            detail: "The app will appear on your home screen"
          }
        ],
        troubleshooting: "Can't find the Share button? Make sure you're using Safari browser (not Chrome or other browsers)."
      },

      chrome_android: {
        title: "Install on Android (Chrome)",
        steps: [
          {
            instruction: "Tap the three dots menu in Chrome",
            icon: "more_vert",
            detail: "Located in the top-right corner"
          },
          {
            instruction: "Select 'Add to Home screen'",
            icon: "add_to_home_screen", 
            detail: "You might also see 'Install app'"
          },
          {
            instruction: "Tap 'Add' to install",
            icon: "check_circle",
            detail: "MapMyLearn will be added to your home screen"
          }
        ],
        troubleshooting: "Don't see 'Add to Home screen'? Try refreshing the page or check if you're using Chrome browser."
      },

      chrome_desktop: {
        title: "Install on Computer (Chrome)",
        steps: [
          {
            instruction: "Look for the install icon in the address bar",
            icon: "install_desktop",
            detail: "Click the computer icon next to the URL"
          },
          {
            instruction: "Click 'Install' in the popup",
            icon: "download",
            detail: "Chrome will download and install the app"
          },
          {
            instruction: "Launch from your desktop or start menu",
            icon: "launch",
            detail: "MapMyLearn will open like a native app"
          }
        ],
        troubleshooting: "No install icon? Try refreshing the page or check Chrome settings to enable app installations."
      },

      edge_desktop: {
        title: "Install on Computer (Edge)",
        steps: [
          {
            instruction: "Click the three dots menu in Edge",
            icon: "more_horiz",
            detail: "Located in the top-right corner"
          },
          {
            instruction: "Select 'Apps' then 'Install this site as an app'",
            icon: "add_to_home_screen",
            detail: "Edge will prepare the installation"
          },
          {
            instruction: "Click 'Install' to complete",
            icon: "check_circle",
            detail: "MapMyLearn will be available in your apps"
          }
        ],
        troubleshooting: "Can't find the install option? Make sure you're using the latest version of Microsoft Edge."
      },

      firefox_manual: {
        title: "Firefox Setup",
        steps: [
          {
            instruction: "Bookmark this page for quick access",
            icon: "bookmark",
            detail: "Press Ctrl+D (Windows) or Cmd+D (Mac)"
          },
          {
            instruction: "Add to bookmark toolbar for easy access",
            icon: "bookmark_border",
            detail: "Right-click bookmark and select 'Add to toolbar'"
          },
          {
            instruction: "Access your courses offline using our Offline page",
            icon: "offline_bolt",
            detail: "Save courses to view them without internet"
          }
        ],
        troubleshooting: "Firefox doesn't support PWA installation, but you can still use all offline features!"
      },

      generic: {
        title: "Alternative Setup",
        steps: [
          {
            instruction: "Bookmark this page for quick access",
            icon: "bookmark",
            detail: "Use your browser's bookmark feature"
          },
          {
            instruction: "Add to your home screen if available",
            icon: "add_to_home_screen",
            detail: "Check your browser's menu for this option"
          },
          {
            instruction: "Use the Offline page to save courses",
            icon: "offline_bolt",
            detail: "Access your learning materials without internet"
          }
        ],
        troubleshooting: "Your browser may have different steps. Look for 'Add to Home Screen' or 'Install' options in the menu."
      }
    },

    // Step 3: Offline Benefits Demonstration
    step3: {
      title: "Learn Anywhere, Anytime",
      subtitle: "See how offline learning works",
      
      demonstration: {
        title: "Your courses work offline!",
        description: "Once you save a course to your history, you can access it even without internet connection.",
        features: [
          {
            icon: "✈️",
            title: "Airplane Mode Ready",
            description: "Study during flights or in areas with poor connectivity"
          },
          {
            icon: "🏕️",
            title: "Perfect for Travel",
            description: "Continue learning while camping, hiking, or exploring"
          },
          {
            icon: "💡",
            title: "Data Saver",
            description: "Reduce mobile data usage by accessing saved content offline"
          },
          {
            icon: "⚡",
            title: "Lightning Fast",
            description: "Offline content loads instantly without waiting for internet"
          }
        ]
      },

      howItWorks: {
        title: "How to use offline learning:",
        steps: [
          "Generate a course and save it to your History",
          "Visit the Offline page from the main menu",
          "Download courses for offline access",
          "Learn anywhere, even without internet!"
        ]
      },

      callToAction: "Ready to try it out?"
    },

    // Step 4: Completion and Next Steps
    step4: {
      title: "You're All Set! 🎉",
      subtitle: "Welcome to the future of mobile learning",
      
      success: {
        title: "Installation Complete!",
        description: "MapMyLearn is now available on your device like a native app.",
        nextSteps: [
          {
            icon: "🎯",
            title: "Create Your First Course",
            description: "Try generating a course on any topic you're interested in"
          },
          {
            icon: "💾", 
            title: "Save to History",
            description: "Keep your favorite courses for easy access later"
          },
          {
            icon: "📱",
            title: "Go Offline",
            description: "Download courses to the Offline page for internet-free learning"
          },
          {
            icon: "🌟",
            title: "Explore Features",
            description: "Try quizzes, AI chat, and audio summaries in your courses"
          }
        ]
      },

      verification: {
        alreadyInstalled: {
          title: "Great! You already have the app installed",
          description: "You're using MapMyLearn as a PWA. Enjoy the full app experience!"
        },
        notDetected: {
          title: "Installation Tips",
          description: "If the app didn't install automatically, you can always bookmark this page and use our offline features."
        }
      },

      tips: {
        title: "Pro Tips for the Best Experience:",
        items: [
          "Use the home screen icon to launch MapMyLearn instantly",
          "Enable notifications to stay on track with your learning goals",
          "Download courses before traveling for uninterrupted learning",
          "Try the AI chat feature for personalized help with any topic"
        ]
      }
    },

    // Status messages and feedback
    status: {
      checkingInstallation: "Checking installation status...",
      installationDetected: "✅ App successfully installed!",
      installationNotDetected: "ℹ️ App may not be installed yet",
      offlineReady: "✅ Offline features are ready to use",
      browserNotSupported: "ℹ️ Your browser has limited PWA support, but offline features still work!"
    },

    // Error messages and fallbacks
    errors: {
      installationFailed: "Installation didn't complete automatically. You can still bookmark this page and use all offline features!",
      browserUnsupported: "Your browser doesn't support app installation, but you can still use MapMyLearn normally and access offline features.",
      genericError: "Something went wrong, but don't worry! You can continue using MapMyLearn in your browser."
    }
  },

  // Legacy PWA fields (for backward compatibility during transition)
  pwaIntroTitle: "MapMyLearn on your device",
  pwaInstall: "Install the app from your browser menu for a full-screen experience.",
  pwaOfflineUsage: "Use the Offline page to access saved courses without an internet connection.",
  pwaIntroGotIt: "Got it!",

  // Tooltip Defaults
  defaultInfoAlt: "More information",
};
