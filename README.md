# MapMyLearn 🗺️🧠 - Your Personal AI Learning Navigator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Live App](https://img.shields.io/badge/Live%20App-mapmylearn.com-brightgreen)](https://mapmylearn.com/)

Tired of scattered information and generic tutorials? MapMyLearn uses cutting-edge AI to build **personalized, structured learning paths** on virtually *any* topic you want to master. Think of it as your personal AI curriculum designer and tutor, available 24/7.

## ✨ Why Use MapMyLearn?

MapMyLearn goes beyond simple search results to deliver a truly effective learning experience:

*   🧠 **Deep Understanding, Not Just Facts:** Our AI doesn't just find links; it analyzes, synthesizes, and structures information into logical modules and submodules, mirroring how expert educators design courses.
*   🌐 **Up-to-Date Knowledge:** We leverage real-time web search (powered by Brave Search) and intelligent scraping to ensure your learning path incorporates current information and diverse perspectives.
*   🚀 **Accelerated Learning:** Get a clear roadmap from beginner to advanced, saving you time figuring out *what* to learn next and *in what order*.
*   💬 **Interactive Learning:** Engage directly with the material through AI-powered chat for each submodule, getting instant clarification and deeper insights. Test your knowledge with automatically generated quizzes.
*   🎧 **Learn On-the-Go:** Generate optional AI-powered audio summaries for submodules to reinforce learning during commutes or workouts.
*   🔒 **Personalized & Private:** Your generated paths are saved securely to your history (if registered), allowing you to track progress and revisit topics anytime.
*   🌍 **Multi-Language Support:** Generate learning paths and interact with the content in multiple languages.

## 🚀 Key Features

*   **AI-Powered Path Generation:** Enter any topic, get a structured course outline with modules and detailed submodules.
*   **Comprehensive Content:** Each submodule features AI-generated explanations synthesized from web research.
*   **Interactive Quizzes:** Automatically generated multiple-choice quizzes to test understanding after each submodule.
*   **AI Submodule Chat:** Ask questions and get explanations specifically tailored to the content of the submodule you're studying.
*   **Curated Resources:** Discover relevant external resources (articles, videos, courses) identified by the AI.
*   **Audio Summaries (Optional):** Generate AI-narrated audio summaries for submodules (requires credits).
*   **User Accounts & History:** Register to save your learning paths, track progress, manage tags, and mark favorites.
*   **PDF Export:** Download your complete learning path as a beautifully formatted PDF document.
*   **Public Sharing:** Share your generated learning paths with others via a unique public link.
*   **Credit System:** Access premium features using a simple credit system, with initial free credits upon registration.
*   **Secure Payments:** Purchase additional credits securely via Stripe.

## 🤔 How It Works (The Magic Behind the Scenes)

1.  **Topic Analysis:** You provide a topic. Our AI analyzes its core concepts, structure, and complexity.
2.  **Targeted Research:** The AI generates specific search queries to gather foundational knowledge, key sub-domains, logical sequencing, practical skills, and common challenges related to your topic, using the Brave Search API.
3.  **Information Synthesis & Structuring:** The AI processes the search results and scraped web content, organizing the information into logical modules (like chapters) and detailed submodules (like lessons).
4.  **Content Generation:** For each submodule, the AI writes comprehensive explanations, synthesizes relevant research, generates quiz questions, and identifies external resources.
5.  **Interactive Delivery:** The complete path, including content, quizzes, chat capabilities, and optional audio, is presented to you in an interactive interface.

## 💡 Technology Sneak Peek

MapMyLearn leverages a sophisticated stack to deliver its powerful features:

*   **AI Core:** Google Gemini, Langchain, LangGraph
*   **Backend:** Python, FastAPI, SQLAlchemy
*   **Frontend:** React, Material UI
*   **Database:** PostgreSQL
*   **Web Search:** Brave Search API
*   **Audio:** OpenAI TTS
*   **Payments:** Stripe
*   *...and many other modern tools!*

## 🚦 Getting Started

Accessing MapMyLearn is simple:

1.  **Visit the Application:** Go to [https://mapmylearn.com/](https://mapmylearn.com/).
2.  **Register (Recommended):** Create a free account to save your learning paths, track progress, use the credit system, and access all features. You'll receive **3 free credits** upon verifying your email!
3.  **Generate a Path:** Navigate to the "Generator", enter your desired topic, select your preferred language and explanation style, and click "Generate Learning Path" (this uses 1 credit).
4.  **Learn:** Explore your personalized path, read content, take quizzes, chat with the AI tutor, and generate audio summaries.
5.  **Save & Organize:** Save paths you like to your history, add tags, and mark favorites.

## 💰 Credits Explained

*   **What they are:** Credits are used to access generation features.
*   **Initial Credits:** New users receive **3 free credits** after email verification.
*   **Costs:**
    *   Generating a new learning path: **1 credit**
    *   Generating an audio summary for one submodule: **1 credit**
    *   Using the submodule chat assistant: **Free** (within daily limits for free tier, allowance for paid users)
    *   Taking quizzes: **Free**
*   **Purchasing:** You can securely purchase additional credits via Stripe through the application interface.

## 🌐 Sharing Your Paths

Want to share a great learning path you generated? Registered users can make their saved paths public, generating a unique shareable link.

## ❓ Support & Feedback

If you encounter any issues or have suggestions, please reach out via email: [pablomiguelargudo@gmail.com](mailto:pablomiguelargudo@gmail.com)

## 🔒 Privacy & Terms

Your privacy is important. Please review our policies:

*   **Privacy Policy:** [https://mapmylearn.com/privacy] <!-- Add actual link -->
*   **Terms and Conditions:** [https://mapmylearn.com/terms]

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.