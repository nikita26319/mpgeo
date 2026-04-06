
  /* MAP */
  const map = L.map('map', { zoomControl: false }).setView([23.5, 78.5], 7);
 L.tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',{
        maxZoom: 20,
        subdomains:['mt0','mt1','mt2','mt3']
}).addTo(map);
  L.control.zoom({ position: 'bottomright' }).addTo(map);



  let layer = null;

  const COLORS = {
    Government: '#4a9eff',
    Private:    '#f5a623',
    PHC:        '#5cb85c',
    CHC:        '#9b7fe8',
    District:   '#00c9a7'
  };

  function colorFor(type) {
    for (const [k, v] of Object.entries(COLORS))
      if (type && type.includes(k)) return v;
    return '#6b8599';
  }

  /* TABS */
  function switchTab(t) {
    document.getElementById('chat-tab').style.display    = t === 'chat'    ? 'flex' : 'none';
    document.getElementById('results-tab').style.display = t === 'results' ? 'flex' : 'none';
    document.getElementById('t-chat').classList.toggle('active',    t === 'chat');
    document.getElementById('t-results').classList.toggle('active', t === 'results');
  }

  /* MESSAGES */
  function addMsg(role, text, sql, count) {
    const wrap = document.getElementById('messages');

    if (role === 'system') {
      const d = document.createElement('div');
      d.className = 'bubble system'; d.textContent = text;
      wrap.appendChild(d);
      wrap.scrollTop = wrap.scrollHeight;
      return;
    }

    const row = document.createElement('div');
    row.className = `msg-wrap ${role}`;

    const av = document.createElement('div');
    av.className = `avatar ${role}`;
    av.textContent = role === 'bot' ? '🤖' : '👤';

    const bub = document.createElement('div');
    bub.className = `bubble ${role}`;
    bub.textContent = text;

    if (sql) {
      const chip = document.createElement('div');
      chip.className = 'sql-chip';
      chip.textContent = sql;
      bub.appendChild(chip);
    }

    if (count !== undefined) {
      const badge = document.createElement('div');
      badge.className = `count-badge ${count > 0 ? 'badge-ok' : 'badge-nil'}`;
      badge.textContent = count > 0 ? `✓ ${count} result${count !== 1 ? 's' : ''} on map` : '⚠ No results found';
      bub.appendChild(document.createElement('br'));
      bub.appendChild(badge);
    }

    row.appendChild(av); row.appendChild(bub);
    wrap.appendChild(row);
    wrap.scrollTop = wrap.scrollHeight;
  }

  function showTyping() {
    const wrap = document.getElementById('messages');
    const row = document.createElement('div');
    row.className = 'typing-wrap'; row.id = 'typing';
    row.innerHTML = `<div class="avatar bot">🤖</div><div class="typing-bubble"><div class="tdot"></div><div class="tdot"></div><div class="tdot"></div></div>`;
    wrap.appendChild(row);
    wrap.scrollTop = wrap.scrollHeight;
  }
  function hideTyping() {
    const el = document.getElementById('typing');
    if (el) el.remove();
  }

  /* RESULTS LIST */
  function fillResults(features, query) {
    const scroll  = document.getElementById('results-scroll');
    const title   = document.getElementById('results-head-title');
    const sub     = document.getElementById('results-head-sub');
    const footer  = document.getElementById('results-footer');
    const badge   = document.getElementById('rbadge');

    scroll.innerHTML = '';

    if (!features || features.length === 0) {
      scroll.innerHTML = `<div id="empty-state"><div class="empty-icon">🔍</div><div class="empty-text">No hospitals found</div><div class="empty-hint">Try a different query</div></div>`;
      title.textContent = 'No results';
      sub.textContent = query;
      footer.style.display = 'none';
      badge.style.display = 'none';
      return;
    }

    title.textContent = `${features.length} Hospital${features.length !== 1 ? 's' : ''} Found`;
    sub.textContent = query;
    badge.textContent = features.length;
    badge.style.display = 'inline';

    let totalBeds = 0;
    features.forEach((f, i) => {
      const p = f.properties;
      const coords = f.geometry?.coordinates;
      totalBeds += parseInt(p.beds) || 0;

      const card = document.createElement('div');
      card.className = 'hcard';
      card.innerHTML = `
        <div class="hcard-num">${i + 1}</div>
        <div class="hcard-dot" style="background:${colorFor(p.type)}"></div>
        <div class="hcard-body">
          <div class="hcard-name">${p.name || '—'}</div>
          <div class="hcard-meta">${p.type || ''} &nbsp;·&nbsp; ${p.district || ''}</div>
        </div>
        <div class="hcard-beds">${p.beds || '—'}</div>
      `;
      if (coords) {
        card.title = `Click to zoom to ${p.name}`;
        card.onclick = () => {
          map.setView([coords[1], coords[0]], 14);
          layer && layer.eachLayer(l => {
            const ll = l.getLatLng();
            if (Math.abs(ll.lat - coords[1]) < 0.001 && Math.abs(ll.lng - coords[0]) < 0.001)
              l.openPopup();
          });
          switchTab('chat');
        };
      }
      scroll.appendChild(card);
    });

    if (totalBeds > 0) {
      footer.style.display = 'block';
      footer.textContent = `Total bed capacity: ${totalBeds.toLocaleString()} beds across ${features.length} hospitals`;
      document.getElementById('stat-beds').textContent = totalBeds.toLocaleString();
      document.getElementById('stat-beds-wrap').style.display = 'flex';
    } else {
      footer.style.display = 'none';
      document.getElementById('stat-beds-wrap').style.display = 'none';
    }
  }

  /* MAP PLOT */
  let routeLayer   = null;
let originMarker = null;

function drawRoute(routeData, origin, hospitals) {
  // Clear previous route
  if (routeLayer)   { map.removeLayer(routeLayer);   routeLayer   = null; }
  if (originMarker) { map.removeLayer(originMarker); originMarker = null; }

  // Origin marker (user location)
  if (origin) {
    originMarker = L.circleMarker([origin.lat, origin.lon], {
      radius: 10, fillColor: '#FF6B00', color: '#fff',
      weight: 3, fillOpacity: 1
    }).addTo(map)
      .bindPopup(`<div style="font-family:'Sora',sans-serif;padding:8px;color:#EAE0D0;background:#0D1F3C">
        <b style="color:#FF6B00">📍 Your Location</b><br/>
        <span style="color:#8A9BB5">${origin.name}</span>
      </div>`)
      .openPopup();
  }

  // Draw route line
  if (routeData?.geojson) {
    routeLayer = L.geoJSON(routeData.geojson, {
      style: {
        color: '#FF6B00', weight: 5,
        opacity: 0.85, dashArray: null,
        lineCap: 'round', lineJoin: 'round'
      }
    }).addTo(map);

    // Fit map to show full route
    const bounds = routeLayer.getBounds();
    if (origin) bounds.extend([origin.lat, origin.lon]);
    map.fitBounds(bounds, { padding: [60, 60] });

    // Show route info on map
    showRouteInfo(routeData, hospitals[0]);
  }
}

function showRouteInfo(route, hospital) {
  let el = document.getElementById('route-info');
  if (!el) {
    el = document.createElement('div');
    el.id = 'route-info';
    el.style.cssText = `
      position:absolute; bottom:22px; right:14px; z-index:1000;
      background:rgba(10,22,40,0.92); backdrop-filter:blur(10px);
      border:1px solid rgba(255,107,0,0.4); border-radius:8px;
      padding:12px 16px; font-family:'Sora',sans-serif;
      border-left: 3px solid #FF6B00; min-width: 200px;
    `;
    document.getElementById('map-zone').appendChild(el);
  }
  el.innerHTML = `
    <div style="font-size:10px;color:#FF6B00;font-family:'JetBrains Mono',monospace;letter-spacing:1px;margin-bottom:6px">FASTEST ROUTE</div>
    <div style="font-size:13px;font-weight:600;color:#EAE0D0;margin-bottom:4px">${hospital?.name || 'Nearest Hospital'}</div>
    <div style="display:flex;gap:16px;margin-top:6px">
      <div>
        <div style="font-size:18px;font-weight:700;color:#F5C842">${route.distance_km} <span style="font-size:11px;color:#8A9BB5">km</span></div>
        <div style="font-size:9px;color:#8A9BB5;text-transform:uppercase;letter-spacing:0.5px">Distance</div>
      </div>
      <div>
        <div style="font-size:18px;font-weight:700;color:#3DB87A">${route.duration_min} <span style="font-size:11px;color:#8A9BB5">min</span></div>
        <div style="font-size:9px;color:#8A9BB5;text-transform:uppercase;letter-spacing:0.5px">Drive time</div>
      </div>
    </div>
  `;
  el.style.display = 'block';
}
function plot(geojson) {
  if (layer) map.removeLayer(layer);
  if (!geojson?.features?.length) return 0;

  layer = L.geoJSON(geojson, {
    pointToLayer: (f, ll) => {
      const color = colorFor(f.properties.type);
      return L.circleMarker(ll, {
        radius: 8,
        fillColor: color,
        color: 'rgba(255,255,255,0.25)',
        weight: 2,
        fillOpacity: 0.92
      });
    },
    onEachFeature: (f, l) => {
      const p = f.properties;
      const color = colorFor(p.type);
      l.bindPopup(`
        <div style="font-family:'Sora',sans-serif;padding:12px 14px;min-width:180px">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:10px">
            <div style="width:8px;height:8px;border-radius:50%;background:${color};box-shadow:0 0 6px ${color}"></div>
            <div style="font-weight:700;font-size:13px;color:#EAE0D0">${p.name}</div>
          </div>
          <div style="font-size:11px;line-height:2;color:#8A9BB5">
            <span style="color:#D4C4A8">Type</span> &nbsp;&nbsp;&nbsp; ${p.type}<br>
            <span style="color:#D4C4A8">Beds</span> &nbsp;&nbsp;&nbsp; <span style="color:#F5C842;font-family:'JetBrains Mono',monospace;font-weight:600">${p.beds}</span><br>
            <span style="color:#D4C4A8">District</span> &nbsp; ${p.district}
          </div>
        </div>`);
    }
  }).addTo(map);

  try { map.fitBounds(layer.getBounds(), { padding:[60,60], maxZoom:13 }); } catch(e) {}

  const n = geojson.features.length;
  // document.getElementById('hval-filt').textContent = n;
  // document.getElementById('hstat-filt').style.display = 'flex';
  // document.getElementById('hdiv-filt').style.display = 'block';
  return n;
}

  /* SEND */
  async function send() {
    const inp = document.getElementById('qinput');
    const btn = document.getElementById('sbtn');
    const query = inp.value.trim();
    if (!query) return;

    inp.value = '';
    btn.disabled = true;
    addMsg('user', query);
    showTyping();

    document.getElementById('query-display').style.display = 'block';
    document.getElementById('query-text').textContent = query;

    try {
      const res  = await fetch('http://localhost:8000/api/geo-query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      });
      const data = await res.json();
      hideTyping();

      const count = plot(data.geojson);
      addMsg('bot', data.summary, data.sql, count);
      fillResults(data.geojson?.features || [], query);

    } catch(e) {
      hideTyping();
      addMsg('bot', '⚠ Cannot reach server. Make sure uvicorn is running on port 8000.');
    }

    btn.disabled = false;
    inp.focus();
  }

  function q(text) {
    document.getElementById('qinput').value = text;
    send();
  }

  document.getElementById('qinput').addEventListener('keydown', e => {
    if (e.key === 'Enter') send();
  });