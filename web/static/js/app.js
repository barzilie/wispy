async function fetchData() {
  try {
    const resp = await fetch('/api/data');
    const data = await resp.json();
    renderDevices(data.devices);
    renderDns(data.dns, data.devices);
    const n = data.devices.length;
    document.getElementById('device-count').textContent =
      `${n} DEVICE${n !== 1 ? 'S' : ''}`;
  } catch (_) {
    // silently retry next tick
  }
}

function renderDevices(devices) {
  const el = document.getElementById('devices-list');
  if (!devices.length) {
    el.innerHTML = '<div class="empty">Waiting for connections...</div>';
    return;
  }
  el.innerHTML = devices.map(d => {
    const name = d.hostname || d.mac;
    const meta  = [d.vendor, d.os_guess].filter(Boolean).join(' / ') || '—';
    const age   = d.last_seen ? d.last_seen.substring(11, 19) + ' UTC' : '';
    return `
      <div class="device-card">
        <div class="device-name">${esc(name)}</div>
        <div class="device-mac">${esc(d.mac)}</div>
        <div class="device-meta">
          <span class="device-ip">${esc(d.ip || '—')}</span>
          &nbsp;·&nbsp;${esc(meta)}
        </div>
        <div class="device-age">last seen ${esc(age)}</div>
      </div>`;
  }).join('');
}

function renderDns(entries, devices) {
  const el = document.getElementById('dns-log');
  if (!entries.length) {
    el.innerHTML = '<div class="empty">No queries captured yet.</div>';
    return;
  }
  const nameMap = {};
  devices.forEach(d => { nameMap[d.mac] = d.hostname || shortMac(d.mac); });

  el.innerHTML = entries.map(r => {
    const time   = r.timestamp ? r.timestamp.substring(11, 19) : '';
    const device = nameMap[r.device_mac] || shortMac(r.device_mac);
    return `
      <div class="dns-entry">
        <span class="dns-time">${esc(time)}</span>
        <span class="dns-device" title="${esc(r.device_mac)}">${esc(device)}</span>
        <span class="dns-domain" title="${esc(r.domain)}">${esc(r.domain)}</span>
      </div>`;
  }).join('');
}

async function getRecommendations() {
  const btn = document.getElementById('recommend-btn');
  const out = document.getElementById('recommend-output');
  btn.disabled = true;
  btn.textContent = '[ ANALYZING... ]';
  out.style.display = 'block';
  out.textContent = 'Querying AI model...';

  try {
    const resp = await fetch('/api/recommend', { method: 'POST' });
    const data = await resp.json();
    out.textContent = data.result;
  } catch (_) {
    out.textContent = 'Error: could not reach recommender.';
  }

  btn.disabled = false;
  btn.textContent = '[ ANALYZE WITH AI ]';
}

function shortMac(mac) {
  return mac ? mac.substring(0, 8) + '…' : '—';
}

function esc(str) {
  return String(str ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}

fetchData();
setInterval(fetchData, 2000);
