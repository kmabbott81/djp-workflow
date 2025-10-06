# Sprint 49 Phase B - Setup Instructions

## 🎯 What You Need To Do Before Leaving

### Step 1: Schedule the Wake Script

**To ensure your computer stays awake during Phase B execution tonight:**

1. **Open File Explorer** and navigate to:
   ```
   C:\Users\kylem\openai-agents-workflows-2025.09.28-v1\
   ```

2. **Find the file:** `setup-phaseB-schedule.ps1`

3. **Right-click** on it and select **"Run as Administrator"**

4. **Click "Yes"** when Windows asks for permission

5. **Verify success** - You should see:
   ```
   [SUCCESS] Scheduled task created!
   Task Name: RelayPhaseBWake
   Trigger: Tonight at 10:00 PM (October 5, 2025)
   ```

6. **Press any key** to close the window

### Step 2: Leave Your Computer On

- ✅ Leave your computer **powered on**
- ✅ Keep it **plugged in** (not on battery)
- ✅ You can **close the laptop lid** (the wake script will handle it)
- ✅ No need to keep any applications open

---

## 📅 What Happens Tonight

### 10:00 PM PDT (Tonight, October 5th, 2025)

**IMPORTANT: Phase B requires manual prompt - it is NOT fully automated**

**Sequence:**

1. **10:00 PM** - Wake script starts automatically (keeps computer awake for 5 hours)
2. **~10:00 PM** - **YOU MUST PROMPT CLAUDE:**
   - Export Prometheus/Grafana baseline data (24-hour monitoring period)
   - Start Phase B execution
3. **~2:00 AM** - Phase B completes (estimated)
4. **3:00 AM** - Wake script ends

**What Gets Built:**
- ✅ Backend `/actions` endpoints deployed to Railway
- ✅ Frontend Studio deployed to Vercel
- ✅ Webhook action fully functional
- ✅ Tests run and validated
- ✅ Documentation created

---

## 📊 At 10 PM Tonight - Your Checklist

**Prompt Claude Code to:**

1. **Export Prometheus/Grafana data** (24-hour baseline monitoring)
   - Save to: `observability/results/2025-10-06-phase-b-24hr/`
   - Export Grafana dashboard JSON (Last 24 hours view)
   - Export Prometheus metrics via Docker

2. **Start Phase B execution**
   - Deploy backend `/actions` endpoints to Railway
   - Deploy frontend Studio to Vercel
   - Run tests and validation
   - Create documentation

---

## 📧 Tomorrow Morning (or after Phase B completes)

Check for:

1. **File:** `C:\Users\kylem\relay-studio\PHASE-B-COMPLETE.md`
   - Contains full results summary
   - Vercel URL for deployed Studio
   - Test results
   - Any issues encountered

2. **Prometheus/Grafana exports:** `observability/results/2025-10-06-phase-b-24hr/`
   - Grafana dashboard JSON files
   - Prometheus backup
   - Screenshots

3. **Git History:** Branch `sprint/49-studio-actions`
   - Check commits from tonight
   - All changes documented

---

## 🛟 If Something Goes Wrong

**Automatic Rollback:**
- Phase B will automatically revert if critical errors occur
- Check `PHASE-B-ERRORS.md` if present

**Manual Rollback (if needed):**
```powershell
# Backend - disable actions
railway variables set ACTIONS_ENABLED=false

# Frontend - revert Vercel deployment
vercel rollback

# Git - revert commits
git log --oneline  # Find commit hash
git revert <hash>
```

---

## ✅ Pre-Flight Checklist Complete

- ✅ All approvals documented
- ✅ Wake script created
- ✅ Testing approach confirmed (Webhook)
- ✅ Build verification passed
- ✅ Time guard set for 10 PM PDT

---

## 📞 Need Help?

If you notice issues tomorrow morning:
1. Review `PHASE-B-COMPLETE.md` or `PHASE-B-ERRORS.md`
2. Check git commits for what changed
3. Use rollback steps above if needed

---

**Current Time:** 9:50 AM PDT, Sunday October 5th, 2025
**Execution Time:** 10:00 PM PDT Tonight (12 hours 10 minutes from now)
**Status:** ⏰ Time Guard Active - All Systems Ready
