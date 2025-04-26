export const helpTexts = {
  // Welcome Modal
  welcomeTitle: "Welcome to MapMyLearn! 👋",
  welcomeValueProp: "Generate personalized learning paths on any topic with the power of AI.",
  welcomeHowItWorks: "How it Works: 1. Enter Topic ➔ 2. AI Generates Path ➔ 3. Learn Interactively (Content, Quiz, Chat).",
  welcomeCredits: (credits) => `Get Started: You have ${credits} free ${credits === 1 ? 'credit' : 'credits'}. Use them to generate paths or audio features.`,
  welcomeGo: "Let's Go!",

  // HomePage
  homeWhyTitle: "Why Choose MapMyLearn?",
  homeWhyDesc: "Our AI-powered platform creates personalized learning experiences that adapt to your specific needs and goals, including structured modules, quizzes, AI chat, and optional audio summaries.",
  homeHowTitle: "How It Works",
  homeHowDesc: "Simply tell us what you want to learn, and our AI will craft a detailed path to guide your studies.", // Existing steps are fine.

  // GeneratorPage
  generatorSubtitle: "Enter any topic. Our AI will build a custom learning path with lessons, activities, and AI chat tailored to you.",

  // HistoryPage
  historyEmptyState: "Your saved learning paths appear here. Generate a new path and click 'Save to History' on the results page to keep track of your learning journey.",

  // LearningPathView
  lpFirstViewAlert: "Explore your new path! Dive into Modules and Submodules. Use the tabs inside submodules for content, quizzes, resources, and AI chat.",

  // Navbar
  navbarCreditsTooltip: (cost) => `Credits are used for generation (1 credit) & audio features (${cost} credit). Purchase more credits anytime.`,
  navbarPurchaseMore: "Purchase more", // Link text if needed, might be separate button

  // LearningPathHeader
  lphSaveTooltip: "Save this path permanently to your History tab to access it later.",

  // SubmoduleCard Tabs
  submoduleTabQuiz: "Test your knowledge on this topic.",
  submoduleTabChat: "Ask the AI specific questions about this submodule's content.",
  submoduleTabAudio: (cost) => `Generate a spoken audio summary of this content (costs ${cost} credit).`,

  // Tooltip Defaults
  defaultInfoAlt: "More information",
}; 