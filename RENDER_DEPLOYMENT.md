# 🚀 Render Deployment Guide with Persistent Storage

## 📋 **Step-by-Step Deployment**

### **1. Create Web Service on Render**
1. Go to [render.com](https://render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect to GitHub: `https://github.com/goblin987/testforwarder`
4. Use these settings:
   - **Name:** `tgcf-pro-bot`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`

### **2. Add Persistent Disk Storage**
1. In your Web Service dashboard
2. Go to **"Settings"** tab
3. Scroll down to **"Persistent Disks"**
4. Click **"Add Persistent Disk"**
5. Configure:
   - **Name:** `tgcf-data`
   - **Size:** `1 GB` (start small, can increase later)
   - **Mount Path:** `/data`

### **3. Set Environment Variables**
In **"Environment"** tab, add:
```env
BOT_TOKEN=your_bot_token_from_botfather
OWNER_USER_ID=your_telegram_user_id
```

### **4. Deploy!**
Click **"Create Web Service"** and wait 2-5 minutes.

## 💾 **What Gets Stored on Persistent Disk**

- **Database:** `/data/tgcf.db` - All account data, campaigns, logs
- **Session Files:** `/data/sessions/` - Telegram session files
- **Logs:** `/data/logs/` - Application logs
- **Backups:** `/data/backups/` - Database backups

## 🔧 **Disk Management**

### **Increase Disk Size:**
1. Go to **"Settings"** → **"Persistent Disks"**
2. Click **"Edit"** on your disk
3. Increase size (e.g., 5GB, 10GB)
4. Click **"Save"**

### **Monitor Usage:**
- Check disk usage in Render dashboard
- Database grows with more accounts/campaigns
- Session files are small (~1KB each)

## ⚠️ **Important Notes**

- **Data Persistence:** Data survives deployments and restarts
- **Backup:** Consider regular database exports
- **Cost:** Persistent disks have additional cost (~$0.25/GB/month)
- **Performance:** Fast SSD storage for optimal performance

## 🆘 **Troubleshooting**

**If disk not mounted:**
- Check mount path is exactly `/data`
- Restart the service
- Check Render logs for errors

**If database errors:**
- Verify disk is mounted: `ls /data`
- Check file permissions
- Restart service

## 📊 **Storage Estimates**

- **Database:** ~1MB per 1000 messages
- **Sessions:** ~1KB per account
- **Logs:** ~10MB per month
- **Recommended:** Start with 1GB, scale as needed
