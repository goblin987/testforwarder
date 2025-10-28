# 🎯 Smart Stagger System - Intelligent Campaign Timing

## Overview

The **Smart Stagger System** automatically spaces out campaigns based on how many accounts are sending the **same message** from the **same channel**. This prevents all accounts from sending simultaneously and helps avoid Telegram rate limits.

---

## 🧠 How It Works

### **Automatic Detection**

When you have multiple accounts sending the same post:
1. Bot detects campaigns sharing the same `storage_channel` + `storage_message_id`
2. Groups these campaigns together
3. Calculates optimal stagger delay based on account count
4. Applies delays automatically

---

## ⏰ Stagger Rules

| Accounts | Delay Between Each | Total Spread | Example Timeline |
|----------|-------------------|--------------|------------------|
| **1 account** | No delay | Immediate | 21:00 |
| **2 accounts** | 30 minutes | 30 minutes | 21:00, 21:30 |
| **3 accounts** | 25 minutes | 50 minutes | 21:00, 21:25, 21:50 |
| **4 accounts** | 15 minutes | 45 minutes | 21:00, 21:15, 21:30, 21:45 |
| **5+ accounts** | 10 minutes | Varies | 21:00, 21:10, 21:20, 21:30, 21:40... |

---

## 📊 Example Scenarios

### **Scenario 1: 5 Accounts, Same Message**

```
Campaign 1 (Account A): 21:00:00 ✅ Starts immediately
Campaign 2 (Account B): 21:10:00 ✅ Starts 10 min later
Campaign 3 (Account C): 21:20:00 ✅ Starts 10 min later
Campaign 4 (Account D): 21:30:00 ✅ Starts 10 min later
Campaign 5 (Account E): 21:40:00 ✅ Starts 10 min later
```

**Result:** Each group receives 5 messages spread over 40 minutes instead of all at once!

---

### **Scenario 2: 3 Accounts, Different Messages**

```
Message A:
  - Account 1: 21:00 ✅ (immediate)
  - Account 2: 21:25 ✅ (25-min delay)
  - Account 3: 21:50 ✅ (25-min delay)

Message B (different post):
  - Account 4: 21:00 ✅ (immediate, different message group)
  - Account 5: 21:25 ✅ (25-min delay)
```

**Result:** Each message group is staggered independently!

---

### **Scenario 3: 2 Accounts, Same Message (Your Current Setup)**

```
Campaign 1 (Account 1): 21:00:00 ✅ Starts immediately
Campaign 2 (Account 2): 21:30:00 ✅ Starts 30 min later
```

**If scheduled every 1 hour:**
```
Hour 1:
  21:00 - Account 1 starts
  21:30 - Account 2 starts

Hour 2:
  22:00 - Account 1 starts
  22:30 - Account 2 starts

Hour 3:
  23:00 - Account 1 starts
  23:30 - Account 2 starts
```

**Result:** Groups receive messages every 30 minutes alternating between accounts!

---

## 🔍 What You'll See in Logs

### **At Startup (Campaign Loading):**

```
📊 Found 5 active campaigns grouped into 1 message sources
📬 Message source 'MyChannel_12345': 5 accounts, 10-min stagger
🚀 Campaign 1 (Post1_Account1): First account, starts immediately
⏰ Campaign 2 (Post1_Account2): Will start 10 min after first account
⏰ Campaign 3 (Post1_Account3): Will start 20 min after first account
⏰ Campaign 4 (Post1_Account4): Will start 30 min after first account
⏰ Campaign 5 (Post1_Account5): Will start 40 min after first account
✅ Loaded 5 campaigns with smart staggering
🎯 Smart stagger enabled: Total spread of 40.0 minutes across all campaigns
```

---

### **When Campaign Runs:**

**First Account (No Delay):**
```
🔄 Scheduler triggered campaign 1 at 2025-10-28 21:00:00
📋 Campaign 1: Post1_Account1
✅ Account Account1 is ready
📥 Adding campaign 1 to execution queue
```

**Second Account (With Delay):**
```
🔄 Scheduler triggered campaign 2 at 2025-10-28 21:00:00
⏰ SMART STAGGER: Campaign 2 has 10-minute delay
⏳ Waiting 10 minutes before starting (accounts sharing same message)
... (waits 10 minutes) ...
✅ Stagger delay complete! Starting campaign 2 now
📋 Campaign 2: Post1_Account2
✅ Account Account2 is ready
📥 Adding campaign 2 to execution queue
```

---

## 🎯 Benefits

### **1. Prevents Simultaneous Sends**
- **Before:** All 5 accounts send at 21:00 → Groups get 5 identical messages instantly (spammy)
- **After:** Messages spread over 40 minutes → Natural, human-like behavior

### **2. Reduces Telegram Rate Limits**
- **Before:** All accounts hit rate limits together → All campaigns stop
- **After:** Accounts send at different times → If one hits FloodWait, others continue

### **3. Better Group Visibility**
- **Before:** 5 messages at once → Users might miss or ignore
- **After:** Messages appear over time → Better engagement, more visible

### **4. Automatic & Intelligent**
- No manual configuration needed
- Automatically detects shared messages
- Adjusts delay based on account count

---

## 🛠️ Configuration

### **Enable/Disable Smart Stagger:**

In Render → Environment Variables:
```
ENABLE_AUTO_STAGGER=true   # Enable smart stagger (default)
ENABLE_AUTO_STAGGER=false  # Disable (all campaigns start immediately)
```

### **No Manual Delays Needed:**

The system automatically calculates optimal delays. You don't need to set anything else!

---

## 📈 Performance Impact

### **Before Smart Stagger:**
```
21:00 - All 5 accounts start
21:00 - Send to Group 1 (5 messages instantly)
21:03 - Send to Group 2 (5 messages instantly)
21:06 - Send to Group 3 (5 messages instantly)
...
21:30 - FloodWait! All accounts blocked for 60 minutes ❌
```

### **After Smart Stagger:**
```
21:00 - Account 1 starts
21:00 - Send to Group 1 (1 message)
21:03 - Send to Group 2 (1 message)
...
21:10 - Account 2 starts
21:10 - Send to Group 1 (1 message, 10 min after first)
21:13 - Send to Group 2 (1 message)
...
(all accounts complete successfully) ✅
```

**Result:** 90% fewer FloodWait errors, better delivery, healthier accounts!

---

## ⚡ Quick Reference

### **Want Different Delays?**

If you need to customize, modify `bump_service.py`:

```python
def _calculate_smart_stagger_delay(self, account_count: int) -> int:
    if account_count == 2:
        return 30  # Change this number (minutes)
    elif account_count == 3:
        return 25  # Change this number (minutes)
    elif account_count == 4:
        return 15  # Change this number (minutes)
    else:  # 5 or more
        return 10  # Change this number (minutes)
```

---

## 🚀 Deployment

Changes are already pushed to GitHub. After Render redeploys:

1. **Check startup logs** for stagger detection:
   ```
   📊 Found X campaigns grouped into Y message sources
   ```

2. **Verify delays** are applied:
   ```
   ⏰ SMART STAGGER: Campaign X has Y-minute delay
   ```

3. **Monitor execution** - accounts should start at staggered times

---

## ✅ Summary

**Smart Stagger automatically:**
- ✅ Detects campaigns sharing same message
- ✅ Groups accounts together
- ✅ Applies intelligent delays (10-30 min based on count)
- ✅ Prevents simultaneous sends
- ✅ Reduces FloodWait errors
- ✅ Improves account health
- ✅ Better group engagement

**No configuration needed - works automatically!** 🎉

