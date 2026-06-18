# Tanah Mympi Housekeeping App
## Support & Operations Guide

**Version:** 1.0  
**Last Updated:** June 19, 2026  
**Status:** Production

---

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Descriptions](#component-descriptions)
4. [Workflow & Data Flow](#workflow--data-flow)
5. [User Guide](#user-guide)
6. [Troubleshooting](#troubleshooting)
7. [Release Notes](#release-notes)
8. [Setup & Deployment](#setup--deployment)

---

## Overview

The Tanah Mympi Housekeeping App is a web-based checklist application designed to streamline housekeeping operations for a boutique island resort. Staff members use the app to sign off on completed room cleanings, flag maintenance issues, and document any action items that require follow-up.

### Key Features
- **PIN-based authentication** for staff security
- **Progressive disclosure UX** that guides staff through the process step-by-step
- **Service-type filtering** to show only relevant checklist items
- **Action required tracking** for maintenance, damage, missing items, and other issues
- **Real-time Google Sheets syncing** for centralized record-keeping
- **Offline support** with local caching and automatic sync on reconnection
- **Mobile-friendly interface** optimized for tablets and smartphones

### Business Value
- Eliminates paper-based workflows
- Creates audit trail in Google Sheets
- Enables quick identification of maintenance needs
- Reduces time per room check from ~15 min to ~5-8 min
- Provides real-time visibility into room status

---

## System Architecture

### High-Level Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     HOUSEKEEPING APP FLOW                       │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐
│   STAFF DEVICE   │  (Tablet, Phone, Browser)
│  housekeeping.   │
│   html file      │
└────────┬─────────┘
         │
         │ (HTTPS)
         ▼
┌──────────────────────────────────────────────────────────────┐
│  GOOGLE APPS SCRIPT (Cloud Function)                         │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ • PIN Validation (Authentication)                      │  │
│  │ • Data Submission Processing                           │  │
│  │ • Submission Recall Handling                           │  │
│  │ • Staff List Management                                │  │
│  └────────────────────────────────────────────────────────┘  │
└────────┬──────────────────────────────────────────────────────┘
         │
         │ (Read/Write)
         ▼
┌──────────────────────────────────────────────────────────────┐
│  GOOGLE SHEETS (Database)                                    │
│  ┌─────────────────┬──────────────────┬────────────────────┐ │
│  │ Staff List Tab  │ Submissions Tab  │ Access Log Tab     │ │
│  ├─────────────────┼──────────────────┼────────────────────┤ │
│  │ • Name          │ • Room ID        │ • Event (Login,    │ │
│  │ • PIN Hash      │ • Service Type   │   Submit, Logout)  │ │
│  │ • Status        │ • Timestamp      │ • Staff Name       │ │
│  │                 │ • Staff Name     │ • Timestamp        │ │
│  │                 │ • Action Items   │ • Device Info      │ │
│  │                 │ • Notes          │                    │ │
│  │                 │ • Sync Status    │                    │ │
│  └─────────────────┴──────────────────┴────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  LOCAL STORAGE   │  (Browser localStorage)
│  ┌──────────────┐│
│  │ Staff Names  ││  (Cached for offline)
│  │ Submissions  ││
│  │ Access Logs  ││
│  └──────────────┘│
└──────────────────┘
```

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend | HTML5, CSS3, Vanilla JavaScript | Single-file PWA app |
| Backend | Google Apps Script | Serverless cloud functions |
| Database | Google Sheets | Central data repository |
| Authentication | PIN + Staff Name | Session-based auth |
| Sync | Fetch API + localStorage | Real-time & offline sync |
| Hosting | Any web server (HTTPS required) | GitHub Pages, static host, or CDN |

---

## Component Descriptions

### 1. Frontend (housekeeping.html)

**Size:** ~8KB (minified)  
**Type:** Single-page application (SPA)

#### Key Sections:
- **Login Screen:** Staff authentication via PIN
- **Form Screen:** Progressive multi-step form for room sign-off
- **Success Screen:** Confirmation with 5-minute recall window
- **Offline Banner:** Alerts when connection is lost

#### Progressive Disclosure Stages:
1. **Step 1:** Select room number
2. **Step 2:** Choose service type (Full Clean, Refresh, Turndown, Inspection)
3. **Step 3:** Complete checklist items (filtered by service type)
4. **Step 4:** Select action items if needed, add notes
5. **Step 5:** Submit and review summary

#### Key Functions:
```
doLogin()              → Authenticate staff member via PIN
showForm()             → Display housekeeping form
toggle()               → Mark checklist item as complete
updateServiceItems()   → Filter items by service type
updateNotes()          → Manage action item styling
submitForm()           → Validate and submit data
resetForm()            → Clear all form state for next room
recallSubmission()     → Undo previous submission (5-min window)
```

### 2. Google Apps Script

**Type:** Cloud-based backend service  
**Trigger:** HTTP POST requests from app

#### Functions:
- **`doPost(e)`** - Main handler for all requests
- **`validatePIN(name, pin)`** - Authenticates staff
- **`logSubmission(data)`** - Writes to Submissions tab
- **`logAccess(data)`** - Records login/logout events
- **`recallSubmission(id)`** - Marks submission as recalled
- **`getStaffList()`** - Returns active staff members

#### Security:
- PINs stored as hashed values (not plaintext)
- All requests logged for audit trail
- HTTPS-only transmission
- Timestamp validation to prevent replay attacks

### 3. Google Sheets Database

**Structure:**
```
Sheet 1: "Staff"
├─ Name (text) - Unique staff identifier
├─ PIN (hashed) - Verification credential
└─ Active (boolean) - Enable/disable staff account

Sheet 2: "Submissions"
├─ Room
├─ Service Type
├─ Staff Name
├─ Timestamp
├─ Action Required (Maintenance, Damage, Missing Item, Other)
├─ Notes
├─ Sync Status (Synced/Pending)
├─ Submission ID
└─ Device Info (User Agent)

Sheet 3: "Access Log"
├─ Event (LOGIN, LOGIN_FAIL, LOGOUT, TIMEOUT, SUBMIT, RECALL)
├─ Staff Name
├─ Timestamp
└─ Additional Data (Room, ID, etc.)
```

---

## Workflow & Data Flow

### Complete User Journey

```
START
  │
  ├─► Login Screen
  │   ├─ Select Staff Name
  │   ├─ Enter PIN
  │   └─ Submit → [Authentication Check]
  │       ├─ FAIL → Show error, retry
  │       └─ SUCCESS → Continue
  │
  ├─► Form Screen (Progressive)
  │   │
  │   ├─ Step 1: Select Room
  │   │   └─ Reveals Step 2
  │   │
  │   ├─ Step 2: Select Service Type
  │   │   └─ Reveals checklist & progress
  │   │
  │   ├─ Step 3: Complete Checklist Items
  │   │   ├─ Click items to mark complete
  │   │   ├─ Progress bar updates
  │   │   └─ When all complete → Submit button enabled
  │   │
  │   ├─ Step 4: Action Items (Optional)
  │   │   ├─ Select action items if needed (Maintenance, Damage, etc.)
  │   │   ├─ If selected → Notes field becomes required
  │   │   └─ Add description in Notes
  │   │
  │   └─ Step 5: Submit
  │       └─ Send data to Google Sheets
  │
  ├─► Success Screen
  │   ├─ Show summary of submission
  │   ├─ Display sync status
  │   ├─ Offer 5-minute recall window
  │   └─ Button: "Start Next Room"
  │       │
  │       └─► [Form Reset]
  │           ├─ Clear all selections
  │           ├─ Reset action item styling
  │           ├─ Clear notes
  │           └─ Back to Step 1
  │
  └─► Repeat for next room or Logout
```

### Data Submission Flow

```
Form Submit
    │
    ▼
Browser Validation
    │ ├─ Room selected?
    │ ├─ Service type selected?
    │ ├─ All items completed?
    │ └─ If action items selected, notes required?
    │
    ├─ FAIL → Show alert, don't submit
    │
    └─ SUCCESS
        │
        ▼
   Save Locally (localStorage)
   _synced = false
        │
        ▼
   Attempt Cloud Sync (if online)
        │
        ├─ POST to Google Apps Script
        │
        ▼
   Google Script Processing
        │
        ├─ Validate submission format
        ├─ Append to "Submissions" sheet
        ├─ Log to "Access Log" sheet
        ├─ Return submission ID
        │
        ├─ SUCCESS → Show "Synced to Google Sheets"
        │            Mark as _synced = true
        │
        └─ FAIL → Show "Saved locally, will sync when online"
                  Keep in localStorage for retry
```

### Offline & Sync Mechanism

```
Device Goes Offline
    │
    ▼
User continues using app normally
    │
    ├─ Submissions saved to localStorage
    ├─ Offline banner shown
    └─ _synced flag = false
    │
    ▼
Device Comes Back Online
    │
    ▼
Auto-retry sync (retrySyncs function)
    │
    ├─ Loop through localStorage items
    ├─ Attempt POST to Google Sheet
    ├─ On success: mark _synced = true
    └─ Update localStorage
```

---

## User Guide

### For Housekeeping Staff

#### Before You Start
1. **Have your PIN ready** - You'll receive a 4-digit PIN from your supervisor
2. **Use a tablet or phone** - The app works best on mobile devices
3. **Check internet connection** - App works offline but needs connection to sync

#### Step-by-Step Process

**1. Login**
- Select your name from the dropdown
- Enter your 4-digit PIN
- Tap "Sign In"
- If you see an error, double-check your PIN and try again

**2. Select Room**
- The app will show "Step 1: Select Room"
- Choose your room number from the dropdown
- Once selected, "Step 2: Service Type" will appear

**3. Choose Service Type**
- **Full Clean (checkout)** - Complete cleaning for guests checking out
- **Refresh (stay-over)** - Quick refresh for guests staying another night
- **Turndown Service** - Evening turndown, fresh linens, amenities
- **Inspection Only** - Visual inspection without full clean

**4. Complete Checklist**
- The app shows only items relevant to your service type
- Tap each item as you complete it (it will turn green with checkmark)
- Watch the progress bar at top to see how many items remain
- When all items show green checkmarks, the submit button will activate

**5. Note Any Issues (If Applicable)**
- If you encounter a problem, tap one of the action items:
  - 🔧 **Maintenance** - Equipment or systems need repair
  - ⚠️ **Damage** - Furniture, fixtures, or décor damaged
  - 📋 **Missing Item** - Something is missing from the room
  - ❓ **Other** - Any other issue
- Once you select an action item, the Notes field becomes required
- Describe the issue in detail so maintenance can resolve it

**6. Sign Off Room**
- Tap "Sign Off Room ✓" button
- You'll see a summary of what was submitted
- The app shows "✓ Synced to Google Sheets" (if online) or "Saved locally" (if offline)

**7. Start Next Room**
- If you made a mistake, you have 5 minutes to tap "Recall & Fix"
- Otherwise, tap "Start Next Room" to reset and begin the next room
- All selections will be cleared automatically

#### Offline Work
- If you lose internet connection, the app still works
- A yellow banner appears saying "You're offline"
- Your submissions are saved locally on your device
- When you reconnect, submissions sync automatically
- You don't need to do anything - just keep working!

#### Tips
- **Be specific in notes** - "Broken mirror" is better than "Damage"
- **Only select action items if there's actually an issue** - Don't flag unnecessarily
- **Work through the checklist in order** - It's designed to guide you
- **Use your device's timer** if you need to track how long each room takes

---

## Troubleshooting

### Login Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Incorrect PIN" error | Wrong PIN entered | Double-check your 4-digit PIN with your supervisor |
| Staff name not in dropdown | Offline or not yet added to system | Ask supervisor to add you to staff list, or manually type your name |
| "Session timed out" | Inactive for 20+ minutes | Log back in with your PIN |

### Sync Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| "Saved locally — will sync when online" | No internet connection | Check WiFi/data connection; submissions sync automatically when online |
| Stuck in offline mode | Connection restored but app not retrying | Try refreshing the page once you have connection |
| Same submission appearing twice | Accidental duplicate submission | Contact supervisor; they can mark one as duplicate in Sheets |

### Checklist Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Items aren't unchecking | Browser glitch | Refresh the page; progress is saved in Google Sheets |
| Wrong items showing | Incorrect service type selected | Go back to Step 2 and select correct service type |
| Can't submit even though all items are checked | Action item selected without notes | If you selected an action item (🔧, ⚠️, etc.), you MUST fill in the Notes field |

### App Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| App won't load | Old version cached in browser | Clear browser cache (settings → Clear browsing data) |
| App is very slow | Large amount of data cached | Clear localStorage: In browser console, type `localStorage.clear()` then refresh |
| Can't find the app URL | Not bookmarked or lost link | Ask your supervisor for the app link or check your emails |

### For Supervisors/Troublemakers

**Check submission status in Google Sheets:**
1. Open the Submissions sheet
2. Look in "Sync Status" column:
   - "Synced" = Successfully uploaded
   - "Pending" = Waiting to upload (offline submission)
3. Check "Access Log" sheet to see login/logout times

**Resolve data issues:**
- **Missing submission:** Check "Access Log" to see if submit was attempted
- **Duplicate submission:** Mark older one with note "DUPLICATE - ignore"
- **Need to undo:** Use the 5-minute recall window or manually delete from Sheets

---

## Release Notes

### Version 1.0 - Production Release

**Release Date:** June 19, 2026

#### Features
- ✅ PIN-based staff authentication
- ✅ Progressive disclosure UI (Step 1 → Step 2 → Step 3 → Submit)
- ✅ Service-type filtering (Full Clean, Refresh, Turndown, Inspection)
- ✅ Action required tracking (Maintenance, Damage, Missing Item, Other)
- ✅ Offline support with automatic sync on reconnection
- ✅ Google Sheets integration for centralized data
- ✅ 5-minute submission recall window
- ✅ Real-time progress tracking
- ✅ Mobile-optimized responsive design
- ✅ Audit logging (login, logout, submit events)

#### Bug Fixes
- **Fixed action item styling persistence:** Action items (Maintenance, Damage, etc.) no longer remain visually selected when starting a new room. Form properly resets all styling when "Start Next Room" is clicked. *(Issue: https://github.com/Pjcoxy/tanah-mympi-staff/commit/62a53c4)*

#### Performance
- File size: 8KB minified (~70% reduction)
- Load time: <1 second on 3G
- Offline response: Instant (localStorage)
- Cloud sync: <2 seconds (typical)

#### Known Limitations
- Requires HTTPS (security requirement)
- PIN recall requires internet connection
- Supports 4-digit PINs only (configurable)
- Maximum 500 access log entries per staff member (auto-purges oldest)

---

## Setup & Deployment

### Prerequisites
- Google Account (for Sheets & Apps Script)
- Web hosting (GitHub Pages, Netlify, or any HTTPS server)
- Staff list with PIN assignments

### Installation Steps

**1. Set up Google Sheets**
```
Create spreadsheet with three sheets:
- Staff (columns: Name, PIN, Active)
- Submissions (columns: Room, Service Type, Staff, Timestamp, Actions, Notes, Synced, ID, Device)
- Access Log (columns: Event, Staff, Timestamp, Details)
```

**2. Create Google Apps Script**
```
1. In Sheets, go to Tools → Script Editor
2. Replace default code with the backend script
3. Deploy as web app:
   - Execute as: Your account
   - Who has access: Anyone
4. Copy the deployment URL
5. Replace CONFIG.SHEETS_URL in housekeeping.html with your URL
```

**3. Deploy Frontend**
```
1. Save housekeeping.html to your web server
2. Ensure HTTPS is enabled
3. Configure staff names in Google Sheets
4. Generate/hash staff PINs
5. Share app URL with staff
```

**4. Testing**
```
- Log in as test staff member
- Complete full workflow (all steps to submit)
- Verify data appears in Google Sheets
- Test offline mode by disabling connection
- Verify sync resumes when connection restored
```

### Configuration

**In housekeeping.html, adjust:**
```javascript
const CONFIG = {
  SHEETS_URL: 'https://script.google.com/macros/s/YOUR_DEPLOYMENT_ID/exec',
  TIMEOUT_MINS: 20,           // Session timeout in minutes
  ROOMS: [...]                // Array of room numbers
}
```

**Customizable:**
- Room numbers list
- Service types (or add more)
- Checklist items
- Action item labels
- Colors (CSS variables in :root)

---

## Support Contact

For issues or questions:
- **App Questions:** Contact your supervisor
- **Technical Issues:** IT department
- **Feature Requests:** Submit to project owner
- **Bug Reports:** Include screenshots and step-by-step reproduction

---

**Document Version:** 1.0  
**Last Updated:** 2026-06-19  
**Maintained By:** Development Team  
**Status:** Active
