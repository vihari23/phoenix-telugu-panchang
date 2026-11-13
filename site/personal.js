'use strict';

const MONTHS = [
  'Chaitra', 'Vaishakha', 'Jyeshtha', 'Ashadha', 'Shravana', 'Bhadrapada',
  'Ashvina', 'Kartika', 'Margashira', 'Pushya', 'Magha', 'Phalguna'
];
const TITHIS = [
  'Pratipat', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami', 'Shashthi',
  'Saptami', 'Ashtami', 'Navami', 'Dashami', 'Ekadashi', 'Dwadashi',
  'Trayodashi', 'Chaturdashi', 'Pournami', 'Amavasya'
];
const STORAGE_KEY = 'phoenix-telugu-personal-tithi-v1';

const byId = id => document.getElementById(id);
const monthSelect = byId('event-maasam');
const tithiSelect = byId('event-tithi');
const pakshaSelect = byId('event-paksham');
const adhikaSelect = byId('event-adhika');
const titleInput = byId('event-title');
const dateInput = byId('english-date');

for (const month of MONTHS) {
  monthSelect.add(new Option(month, month));
}
for (const tithi of TITHIS) {
  tithiSelect.add(new Option(tithi, tithi));
}
tithiSelect.value = 'Panchami';

let records = [];
let recordMap = new Map();
let storedEvents = [];

function readSavedEvents() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const decoded = raw ? JSON.parse(raw) : [];
    if (Array.isArray(decoded)) {
      storedEvents = decoded.filter(event =>
        event && typeof event.id === 'string' &&
        typeof event.title === 'string' &&
        MONTHS.includes(event.maasam) &&
        ['Shukla', 'Krishna'].includes(event.paksham) &&
        TITHIS.includes(event.tithi) &&
        ['regular', 'adhika', 'both'].includes(event.adhika_policy)
      );
    }
  } catch (error) {
    byId('form-status').textContent = 'Browser storage could not be loaded. Check private browsing settings.';
  }
}

function saveEvents() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(storedEvents));
    return true;
  } catch (error) {
    byId('form-status').textContent = 'This browser did not allow local storage. Nothing was saved.';
    return false;
  }
}

function normalizedTithi(day) {
  const original = day.tithi;
  if (original === 'Amavasya' || original === 'Pournami') {
    return original;
  }
  if (original.endsWith(' Ekadashi')) {
    return 'Ekadashi';
  }
  return original.replace(/^(Shukla|Krishna)\s+/, '');
}

function normMonth(month) {
  return month.replace(/^(?:Nija|Adhika)\s+/, '');
}

function monthMatches(actual, event) {
  if (event.adhika_policy === 'adhika') {
    return actual === 'Adhika ' + event.maasam;
  }
  if (event.adhika_policy === 'both') {
    return normMonth(actual) === event.maasam;
  }
  return actual === event.maasam || actual === 'Nija ' + event.maasam;
}

function isMatch(day, event) {
  return monthMatches(day.maasam, event) &&
    day.paksham === event.paksham &&
    normalizedTithi(day) === event.tithi;
}

function daysApart(left, right) {
  const a = Date.parse(left + 'T00:00:00Z');
  const b = Date.parse(right + 'T00:00:00Z');
  return Math.round((b - a) / 86400000);
}

function occurrences(event) {
  let previous = null;
  const result = [];
  for (const day of records) {
    if (!isMatch(day, event)) {
      continue;
    }
    if (previous !== null && daysApart(previous, day.date) === 1) {
      continue; // A tithi can be present at two successive sunrises.
    }
    result.push(day);
    previous = day.date;
  }
  return result;
}

function todayInPhoenix() {
  const fields = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Phoenix', year: 'numeric', month: '2-digit', day: '2-digit'
  }).formatToParts(new Date());
  const value = type => fields.find(part => part.type === type).value;
  return value('year') + '-' + value('month') + '-' + value('day');
}

function friendlyDate(isoDate) {
  const date = new Date(isoDate + 'T12:00:00Z');
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
    timeZone: 'UTC'
  }).format(date);
}

function makeText(tag, value) {
  const element = document.createElement(tag);
  element.textContent = value;
  return element;
}

function render() {
  const list = byId('event-list');
  list.replaceChildren();
  const disabled = !records.length || !storedEvents.length;
  byId('download-ics').disabled = disabled;
  byId('clear-events').disabled = !storedEvents.length;
  if (!storedEvents.length) {
    list.appendChild(makeText('p', 'No personal events saved. Add one above.'));
    return;
  }
  for (const event of storedEvents) {
    const row = document.createElement('div');
    row.className = 'record';
    row.appendChild(makeText('strong', event.title));
    const policy = event.adhika_policy === 'regular' ? 'Regular/Nija month' :
      event.adhika_policy === 'adhika' ? 'Adhika month only' : 'Regular + Adhika';
    row.appendChild(makeText(
      'div', event.maasam + ' · ' + event.paksham + ' · ' + event.tithi + ' · ' + policy
    ));
    const found = occurrences(event);
    const next = found.filter(item => item.date >= todayInPhoenix());
    const upcoming = next.slice(0, 4);
    const line = upcoming.length ?
      'Upcoming: ' + upcoming.map(item => friendlyDate(item.date)).join(' · ') :
      'No upcoming matching date in the current published window';
    const small = makeText('div', records.length ? line : 'Dates will appear after the feed loads.');
    small.className = 'small muted';
    row.appendChild(small);
    const deleteButton = makeText('button', 'Delete');
    deleteButton.className = 'danger';
    deleteButton.type = 'button';
    deleteButton.style.marginTop = '.65rem';
    deleteButton.addEventListener('click', () => {
      storedEvents = storedEvents.filter(item => item.id !== event.id);
      if (saveEvents()) {
        render();
      }
    });
    row.appendChild(deleteButton);
    list.appendChild(row);
  }
}

function validEntry(event) {
  if (!event.title || event.title.trim().length > 100) {
    return 'Please enter an event name (1–100 characters).';
  }
  if (event.tithi === 'Pournami' && event.paksham !== 'Shukla') {
    return 'Pournami belongs to Shukla paksham.';
  }
  if (event.tithi === 'Amavasya' && event.paksham !== 'Krishna') {
    return 'Amavasya belongs to Krishna paksham.';
  }
  return '';
}

byId('lookup-date').addEventListener('click', () => {
  const iso = dateInput.value;
  const day = recordMap.get(iso);
  if (!iso) {
    byId('lookup-status').textContent = 'Choose a Gregorian date first.';
    return;
  }
  if (!day) {
    byId('lookup-status').textContent =
      'This date is outside the currently published Phoenix calendar. Choose the lunar details manually.';
    return;
  }
  monthSelect.value = normMonth(day.maasam);
  pakshaSelect.value = day.paksham;
  tithiSelect.value = normalizedTithi(day);
  adhikaSelect.value = day.maasam.startsWith('Adhika ') ? 'adhika' : 'regular';
  byId('lookup-status').textContent = friendlyDate(iso) + ': ' +
    day.maasam + ' · ' + day.paksham + ' · ' + day.tithi + ' (Phoenix sunrise).';
});

byId('add-event').addEventListener('click', () => {
  const event = {
    id: (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + '-' +
      Math.floor(Math.random() * 1000000)),
    title: titleInput.value.trim(),
    maasam: monthSelect.value,
    paksham: pakshaSelect.value,
    tithi: tithiSelect.value,
    adhika_policy: adhikaSelect.value
  };
  const invalid = validEntry(event);
  if (invalid) {
    byId('form-status').textContent = invalid;
    return;
  }
  storedEvents.push(event);
  if (!saveEvents()) {
    storedEvents.pop();
    return;
  }
  byId('form-status').textContent = 'Saved on this device only.';
  titleInput.value = '';
  render();
});

byId('clear-events').addEventListener('click', () => {
  if (!window.confirm('Delete all personal events saved in this browser?')) {
    return;
  }
  storedEvents = [];
  if (saveEvents()) {
    render();
  }
});

function escapeIcs(value) {
  return String(value).replace(/\\/g, '\\\\')
    .replace(/\r?\n/g, '\\n')
    .replace(/,/g, '\\,')
    .replace(/;/g, '\\;');
}

function foldLine(line) {
  const encoder = new TextEncoder();
  const parts = [];
  let chunk = '';
  let length = 0;
  for (const character of line) {
    const size = encoder.encode(character).length;
    if (length + size > 75) {
      parts.push(chunk);
      chunk = ' ';
      length = 1;
    }
    chunk += character;
    length += size;
  }
  parts.push(chunk);
  return parts.join('\r\n');
}

function makeCalendar() {
  const events = [
    'BEGIN:VCALENDAR', 'VERSION:2.0',
    'PRODID:-//Phoenix Personal Telugu Tithi Calendar//EN',
    'CALSCALE:GREGORIAN',
    'X-WR-CALNAME:My Telugu Tithi Dates - Phoenix',
    'X-WR-TIMEZONE:America/Phoenix'
  ];
  const timestamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
  for (const entry of storedEvents) {
    for (const match of occurrences(entry)) {
      const start = match.date.replace(/-/g, '');
      events.push(
        'BEGIN:VEVENT',
        'UID:' + entry.id + '-' + start + '@phoenix-telugu-personal-local',
        'DTSTAMP:' + timestamp,
        'DTSTART:' + start + 'T150000Z',
        'DTEND:' + start + 'T160000Z',
        'SUMMARY:' + escapeIcs(entry.title),
        'DESCRIPTION:' + escapeIcs(
          match.maasam + ' Maasam; ' + match.paksham + ' Paksham; ' +
          match.tithi + '. Based on Phoenix sunrise; verify family observance rules.'
        ),
        'END:VEVENT'
      );
    }
  }
  events.push('END:VCALENDAR');
  return events.map(foldLine).join('\r\n') + '\r\n';
}

byId('download-ics').addEventListener('click', () => {
  const content = makeCalendar();
  const blob = new Blob([content], { type: 'text/calendar;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = 'my-phoenix-telugu-tithi-dates.ics';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  byId('form-status').textContent =
    'Downloaded an ICS for the currently published dates. This import does not auto-refresh.';
});

async function loadDays() {
  try {
    const response = await fetch('./phoenix-day-index.json', { cache: 'no-cache' });
    if (!response.ok) {
      throw new Error('HTTP ' + response.status);
    }
    const data = await response.json();
    if (data.city !== 'Phoenix' || !Array.isArray(data.days)) {
      throw new Error('Unexpected calendar data');
    }
    records = data.days;
    recordMap = new Map(records.map(day => [day.date, day]));
    const first = records[0] && records[0].date;
    const last = records[records.length - 1] && records[records.length - 1].date;
    byId('range-status').textContent =
      'Calculated dates: ' + friendlyDate(first) + ' through ' + friendlyDate(last) +
      '. New dates are published each month.';
  } catch (error) {
    byId('range-status').textContent =
      'Could not load Phoenix lunar dates. Please try reloading this page. ' + error.message;
    byId('lookup-status').textContent = 'Date lookup is currently unavailable.';
  }
  render();
}

readSavedEvents();
render();
loadDays();
