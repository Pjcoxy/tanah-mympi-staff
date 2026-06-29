// Tanah Mympi — Housekeeping backend (Google Apps Script)
//
// This is a COPY of the Apps Script that powers the app, kept here for version
// control. The live version lives in a standalone Apps Script project:
//   https://script.google.com/d/1F7ZbhlHNl_BI9W0_mOkN9hWfAHSKHNOO5w9Ul4LsvfZRsAs_wgpGWpAy/edit
// After editing here, paste into that project and deploy a NEW VERSION of the
// existing deployment (Deploy > Manage deployments > edit > Version: New version)
// so the /exec URL stays the same.

const SHEET_ID = '19lrq6Sp7wY0q74mtZd0VDgLwj4QGu1Vf-LUEEMDzbPY';

function doGet(e) {
  const action = (e && e.parameter && e.parameter.action) ? e.parameter.action : '';
  if (action === 'records') return json({ records: getRecords() });
  return json({ names: getStaffNames() });
}

function getStaffNames() {
  const staffSheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Staff');
  if (!staffSheet) return [];
  const rows = staffSheet.getDataRange().getValues();
  return rows.slice(1)
    .filter(r => String(r[2]).toLowerCase() === 'yes' && r[0])
    .map(r => String(r[0]));
}

// Returns every row from the Records sheet (used by dashboard.html).
// Only operational fields are returned — never staff PINs.
function getRecords() {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Records');
  if (!sheet || sheet.getLastRow() < 2) return [];
  const rows = sheet.getDataRange().getValues();
  return rows.slice(1).map(r => ({
    type: r[0],
    timestamp: (r[1] instanceof Date) ? formatTs(r[1]) : r[1],
    staff: r[2],
    room: r[3],
    serviceType: r[4],
    actionRequired: r[5]
  }));
}

// Keep date output in the script's timezone and in the same human format the
// app writes, so the dashboard parses it consistently (avoids UTC day-shift).
function formatTs(d) {
  return Utilities.formatDate(d, Session.getScriptTimeZone(), 'd MMMM yyyy, h:mm a');
}

function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  if (data.action === 'login')  return json(handleLogin(data));
  if (data.action === 'submit') return json(handleSubmit(data));
  if (data.action === 'recall') return json(handleRecall(data));
  return json({ ok: false, error: 'Unknown action' });
}

function handleLogin(data) {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Staff');
  if (!sheet) return { ok: false };
  const rows = sheet.getDataRange().getValues();
  for (let i = 1; i < rows.length; i++) {
    if (rows[i][0] === data.name && String(rows[i][1]) === String(data.pin) && String(rows[i][2]).toLowerCase() === 'yes') {
      logEvent('LOGIN', data.name, data.timestamp || now());
      return { ok: true };
    }
  }
  logEvent('LOGIN_FAIL', data.name || 'unknown', data.timestamp || now());
  return { ok: false };
}

function handleSubmit(data) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sheet = ss.getSheetByName('Records') || ss.insertSheet('Records');

  if (sheet.getLastRow() === 0) {
    const h = ['Type','Timestamp','Staff Member','Room','Service Type','Action Required','Notes','Device'];
    sheet.appendRow(h);
    sheet.getRange(1,1,1,h.length).setFontWeight('bold').setBackground('#1a4a5c').setFontColor('#ffffff');
    sheet.setFrozenRows(1);
  }

  const id = Date.now().toString(36) + Math.random().toString(36).slice(2,5);
  sheet.appendRow([
    'SUBMISSION',
    data.timestamp,
    data.staff,
    data.room,
    data.serviceType,
    data.actionRequired,
    data.notes,
    data.userAgent
  ]);

  return { ok: true, id };
}

function handleRecall(data) {
  logEvent('RECALL', 'Unknown', now(), 'ID ' + data.id);
  return { ok: true };
}

function logEvent(event, staff, timestamp, details) {
  const ss = SpreadsheetApp.openById(SHEET_ID);
  let sheet = ss.getSheetByName('Records') || ss.insertSheet('Records');

  if (sheet.getLastRow() === 0) {
    const h = ['Type','Timestamp','Staff Member','Room','Service Type','Action Required','Notes','Device'];
    sheet.appendRow(h);
    sheet.getRange(1,1,1,h.length).setFontWeight('bold').setBackground('#1a4a5c').setFontColor('#ffffff');
    sheet.setFrozenRows(1);
  }

  sheet.appendRow([event, timestamp, staff, '', '', '', details || '', '']);
}

function now() {
  return new Date().toLocaleString('en-AU', {
    day:'numeric', month:'short', year:'numeric',
    hour:'2-digit', minute:'2-digit'
  });
}

function json(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
