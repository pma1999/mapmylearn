# Deployment Guide for Learny

This guide explains how to deploy the Learny application using Vercel for the frontend and Railway for the backend.

## Prerequisites

- [Vercel Account](https://vercel.com)
- [Railway Account](https://railway.app)
- [GitHub Account](https://github.com)
- OpenAI API Key
- Tavily API Key

## Deploying the Backend to Railway

### Option 1: Deploy via Railway Dashboard

1. **Push your code to GitHub**
   
   Make sure your project is in a GitHub repository.

2. **Create a new project in Railway**

   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project" and select "Deploy from GitHub repo"
   - Select your repository
   - Railway will automatically detect the configuration from `railway.json` and `Procfile`

3. **Configure environment variables**

   In the Railway dashboard, add the following environment variables:
   
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `TAVILY_API_KEY`: Your Tavily API key
   - `FRONTEND_URL`: Your Vercel frontend URL (once deployed)
   - Any other environment variables needed by your application

4. **Deploy the backend**

   Railway will automatically deploy your application based on the configuration in `railway.json`.

5. **Get your backend URL**

   Once deployed, Railway will provide you with a URL for your backend service. Note this URL as you'll need it for the frontend configuration.

### Option 2: Deploy via Railway CLI

1. **Install Railway CLI**

   ```bash
   npm i -g @railway/cli
   ```

2. **Login to Railway**

   ```bash
   railway login
   ```

3. **Initialize your project**

   ```bash
   railway init
   ```

4. **Link to an existing project (if you already created one in the dashboard)**

   ```bash
   railway link
   ```

5. **Set environment variables**

   ```bash
   railway variables set OPENAI_API_KEY=your_openai_api_key
   railway variables set TAVILY_API_KEY=your_tavily_api_key
   railway variables set FRONTEND_URL=your_vercel_frontend_url
   ```

6. **Deploy the application**

   ```bash
   railway up
   ```

7. **Get your deployment URL**

   ```bash
   railway status
   ```

## Deploying the Frontend to Vercel

1. **Update the API URL in vercel.json**

   In the `frontend/vercel.json` file, replace `https://your-railway-app-name.railway.app` with your actual Railway backend URL.

2. **Push changes to GitHub**

   Make sure all changes are committed and pushed to your GitHub repository.

3. **Create a new project in Vercel**

   - Go to [Vercel Dashboard](https://vercel.com/dashboard)
   - Click "Add New" > "Project"
   - Import your GitHub repository
   - Configure the project:
     - Root Directory: `frontend`
     - Build Command: `npm run build`
     - Output Directory: `build`

4. **Configure environment variables**

   In the Vercel dashboard, add the following environment variables:
   
   - `REACT_APP_API_URL`: Your Railway backend URL

5. **Deploy the frontend**

   Click "Deploy" and Vercel will build and deploy your frontend application.

## Connecting Frontend and Backend

1. **Update Railway environment variables**

   Once your frontend is deployed, go back to Railway and add your Vercel frontend URL to the `FRONTEND_URL` environment variable.

2. **Verify the connection**

   Visit your Vercel frontend URL and ensure it can communicate with the backend by testing the generation of a learning path.

## Troubleshooting

- **CORS Issues**: Ensure the `allowed_origins` in `api.py` includes your Vercel domain
- **API Connection Failures**: Check that environment variables are set correctly on both platforms
- **Deployment Failures**: 
  - On Railway: Check logs in the Railway dashboard
  - On Vercel: Check build logs in the Vercel dashboard

## Custom Domains (Optional)

Both Vercel and Railway support custom domains:

- **Vercel**: Go to your project settings > Domains to add a custom domain
- **Railway**: Go to your project settings > Domains to add a custom domain

If you add custom domains, remember to update the corresponding environment variables and CORS settings. 