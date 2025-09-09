#!/bin/bash

echo ""
echo "========================================"
echo "   TELEGRAM BOT AUTO DEPLOYMENT"
echo "========================================"
echo ""

# Check if we're in a git repository
if ! git status >/dev/null 2>&1; then
    echo "ERROR: This directory is not a Git repository!"
    echo "Please run: git init"
    echo "Then add your GitHub repository: git remote add origin YOUR_REPO_URL"
    exit 1
fi

echo "Current status:"
git status --porcelain

echo ""
echo "Adding all changes to git..."
git add .

echo ""
read -p "Enter commit message (or press Enter for default): " commit_message
if [ -z "$commit_message" ]; then
    commit_message="Update bot with new features"
fi

echo ""
echo "Committing changes..."
git commit -m "$commit_message"

echo ""
echo "Pushing to GitHub (main branch)..."
git push origin main

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Failed to push to GitHub!"
    echo "Make sure you have:"
    echo "1. Added the GitHub repository as remote origin"
    echo "2. Have proper authentication set up"
    echo ""
    echo "To set up GitHub repository:"
    echo "git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git"
    echo ""
    exit 1
fi

echo ""
echo "========================================"
echo "   SUCCESS! Changes pushed to GitHub"
echo "========================================"
echo ""
echo "Your bot will automatically deploy on Render within 2-3 minutes."
echo "Check your Render dashboard for deployment status."
echo ""
