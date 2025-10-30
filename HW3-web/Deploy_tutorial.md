# Stockcord: Step-by-Step Deployment Guide for Render

This guide provides a detailed, step-by-step tutorial for deploying the Stockcord application to the Render cloud platform. It covers setting up the required cloud database on MongoDB Atlas and configuring the services on Render.

## Prerequisites

Before you begin, ensure you have the following:
- A GitHub account with the Stockcord project code pushed to a repository.
- A free account on [MongoDB Atlas](https://www.mongodb.com/cloud/atlas).
- A free account on [Render](https://render.com/).

The deployment process is divided into two main phases: **Database Setup** and **Application Deployment**.

---

## Phase 1: MongoDB Atlas - Cloud Database Setup

Our application requires a cloud-hosted database that can be accessed from anywhere on the internet. We will use MongoDB Atlas's free tier for this.

### Step 1.1: Create a Free Database Cluster

A "Cluster" is MongoDB's term for a set of servers that run your database.

1.  **Log in** to your MongoDB Atlas account.
2.  If you don't have a project, create a new **Project**.
3.  From your project's main dashboard, click the **"Create"** button (or "Build a Database").
4.  On the "Deploy your database" page, select the **M0 (Free)** plan under the "Shared" tab. This is a permanent free tier.
5.  **Cloud Provider & Region**: Keep the default (AWS) and choose a region geographically close to you or your users (e.g., `ap-southeast-1 (Singapore)`).
6.  **Cluster Name**: You can leave the default `Cluster0` or give it a descriptive name like `StockcordCluster`.
7.  Click **"Create Cluster"**. The provisioning process will take approximately 3-5 minutes.

### Step 1.2: Create a Database User

Your application needs credentials to log in to the database.

1.  In the left-hand navigation pane, under the **SECURITY** section, click **"Database Access"**.
2.  Click the **"Add New Database User"** button.
3.  **Authentication Method**: Choose **Password**.
4.  **Credentials**:
    -   **Username**: Enter a username, for example, `stockcord_user`.
    -   **Password**: Click "Autogenerate Secure Password" or create your own. **Crucially, copy this password and save it in a secure location.** You will need it for the connection string.
5.  **Privileges**: Under "Database User Privileges", select **"Read and write to any database"**.
6.  Click **"Add User"**.

### Step 1.3: Configure Network Access (The Most Common Point of Failure)

This step tells Atlas to allow connections from Render's servers.

1.  In the left-hand navigation pane, under **SECURITY**, click **"Network Access"**.
2.  Click the **"Add IP Address"** button.
3.  In the pop-up window, click **"ALLOW ACCESS FROM ANYWHERE"**.
    -   The IP Address field will automatically be populated with `0.0.0.0/0`.
    -   This is necessary because Render's servers have dynamic IP addresses.
4.  Click **"Confirm"** and wait for the status of the new entry to change from "Pending" to **"Active"**.

### Step 1.4: Get and Assemble Your Final Connection String (`MONGO_URI`)

This is the final piece of information we need from Atlas.

1.  Navigate back to the **DATABASE** section from the left-hand pane.
2.  Find your newly created cluster and click the **"Connect"** button.
3.  In the "Choose a connection method" window, select **"Drivers"**.
4.  Under "Connect to your application", you will see a connection string. **Copy this string.** It will look like this:
    ```
    mongodb+srv://<username>:<password>@<cluster-url>/?retryWrites=true&w=majority
    ```
5.  Now, assemble your final `MONGO_URI` by making two modifications:
    -   Replace `<username>` with the username you created in Step 1.2.
    -   Replace `<password>` with the **password you saved** in Step 1.2.
    -   **Add your database name (`stock_portfolio_db`)** between the `/` and the `?`.

    Your final, complete `MONGO_URI` will look like this:
    ```
    mongodb+srv://stockcord_user:YOUR_SAVED_PASSWORD@stockcordcluster.xxxxx.mongodb.net/stock_portfolio_db?retryWrites=true&w=majority
    ```
**Keep this final `MONGO_URI` ready. You will need it in the next phase.**

---

## Phase 2: Render - Application Deployment

Now we will configure Render to run the application from your GitHub repository.

### Step 2.1: Create the Web Service

This service will run your Flask application and serve the website.

1.  **Log in** to your Render Dashboard.
2.  Click **"New +"** in the top-right corner and select **"Web Service"**.
3.  **Connect Repository**: Click "Build and deploy from a Git repository" and select your Stockcord project repository.
4.  **Configure Service Details**:
    -   **Name**: `stockcord` (this will be part of your public URL).
    -   **Region**: Choose a region (ideally the same one you chose in Atlas).
    -   **Root Directory**: **Leave this blank** if your `app.py` is in the main directory. If it's in a subfolder like `HW3-web`, enter the subfolder name here.
    -   **Runtime**: `Python 3`.
    -   **Build Command**: `pip install -r requirements.txt`.
    -   **Start Command**: `gunicorn app:app` (Render should auto-detect this from your `Procfile`).
5.  **Instance Type**: Select the **Free** plan.
6.  **Add Environment Variables**:
    -   Scroll down and expand the **"Advanced"** section.
    -   Click **"Add Environment Variable"** four times to create the following key-value pairs:
        -   **Key**: `MONGO_URI`
            -   **Value**: Paste the **final, complete `MONGO_URI`** you assembled in Phase 1.
        -   **Key**: `FINNHUB_API_KEY`
            -   **Value**: Paste your Finnhub API key.
        -   **Key**: `SECRET_KEY`
            -   **Value**: Generate a new, random, long string for production.
        -   **Key**: `PYTHON_VERSION`
            -   **Value**: `3.10.13`
7.  **Create the Service**: Scroll to the bottom and click **"Create Web Service"**.

Render will now start building and deploying your application. This may take several minutes.

### Step 2.2: Create the Background Worker

This service will run the `update_prices.py` script periodically to keep your data fresh.

1.  On the Render Dashboard, click **"New +"** -> **"Background Worker"**.
2.  **Connect Repository**: Select the same GitHub repository as before.
3.  **Configure Worker Details**:
    -   **Name**: `stockcord-updater`.
    -   **Region**: Choose the same region as your Web Service.
    -   **Runtime**: `Python 3`.
    -   **Build Command**: `pip install -r requirements.txt`.
    -   **Start Command**: `python update_prices.py`.
4.  **Instance Type**: Select the **Free** plan. (Free background workers do not sleep).
5.  **Add Environment Variables**:
    -   Expand **"Advanced"** and add the **same** `MONGO_URI`, `FINNHUB_API_KEY`, and `PYTHON_VERSION` variables as you did for the Web Service.
6.  **Create the Worker**: Click **"Create Background Worker"**.

---

## Phase 3: Final Verification

1.  **Monitor Logs**: Go to the "Logs" tab for both your `stockcord` Web Service and `stockcord-updater` Background Worker.
    -   The Web Service log should show `Successfully connected to MongoDB.` and `Your service is live 🎉`.
    -   The Background Worker log should show the output of the `update_prices.py` script, such as "Found X unique symbols to update...".
2.  **Access Your Live Site**:
    -   On your `stockcord` Web Service page, find the public URL at the top (e.g., `https://stockcord.onrender.com`).
    -   Click the link. The first visit may take 20-30 seconds for the free service to "wake up".
3.  **Test Functionality**:
    -   Register a new account and log in.
    -   Add a transaction.
    -   The data should appear on your dashboard, reflecting the prices fetched by the background worker.

**Congratulations! Your Stockcord application is now live.**