# TgCF Pro - Changelog

## Version 1.1.0 - Bug Fixes & Improvements

### 🐛 Bug Fixes

#### Fixed Campaign Scheduling Issue
- **Problem**: Campaigns were only sending once instead of repeating on schedule
- **Solution**: Implemented proper background scheduler thread with `schedule.run_pending()`
- **Impact**: Campaigns now repeat correctly every X minutes/hours as configured

#### Fixed Interactive Button Visibility
- **Problem**: Buttons were coded but not appearing in group messages
- **Solution**: 
  - Improved button creation logic with proper Telethon Button.url() formatting
  - Added fallback mechanism for groups that don't support buttons
  - Enhanced error handling and logging for button-related issues
- **Impact**: Interactive buttons now appear correctly under campaign messages

### ✨ Improvements

#### Enhanced Scheduler
- Added proper background thread for campaign execution
- Improved scheduling logic with better error handling
- Added support for simple numeric minute intervals (e.g., "3" = 3 minutes)
- Better logging for scheduled campaign execution

#### Better Button Support
- Support for multiple button rows (2 buttons per row)
- Automatic fallback to text-only messages if buttons fail
- Improved button parsing and error handling
- Support for both URL buttons and inline callback buttons

#### Improved Logging
- More detailed logging for campaign execution
- Better error messages for troubleshooting
- Visual indicators (emojis) for different log levels

### 🧪 Testing
- Added test script (`test_fixes.py`) to verify fixes
- Campaign scheduling now properly repeats every 3 minutes
- Buttons appear correctly in supported groups/channels

### 📝 Technical Details

**Files Modified:**
- `bump_service.py`: Fixed scheduler and button logic
- Added comprehensive error handling and logging

**New Features:**
- Automatic scheduler thread management
- Improved button creation with fallback support
- Enhanced custom scheduling (supports "3 minutes", "every 3 minutes", or just "3")

---

## How to Test the Fixes

1. **Test Campaign Scheduling:**
   ```bash
   python test_fixes.py
   ```

2. **Test Button Functionality:**
   - Create a campaign with buttons through the bot
   - Verify buttons appear in the sent messages
   - Check logs for button creation success/failure

3. **Test 3-Minute Repeating:**
   - Create a campaign with "custom" schedule type
   - Set schedule time to "3 minutes" or just "3"
   - Campaign should repeat every 3 minutes automatically
