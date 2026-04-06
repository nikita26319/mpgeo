
// Update the send() function to handle routing response
async function send() {
  const inp   = document.getElementById('qinp');
  const btn   = document.getElementById('sbtn');
  const query = inp.value.trim();
  if (!query) return;

  inp.value = ''; btn.disabled = true;
  addMsg('user', query);
  showTyping();

  document.getElementById('last-query').style.display = 'block';
  document.getElementById('lqtext').textContent = query;

  // Clear old route info
  const ri = document.getElementById('route-info');
  if (ri) ri.style.display = 'none';

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

    // Draw route if present
    if (data.route && data.origin) {
      drawRoute(data.route, data.origin, data.geojson?.features || []);
    }

  } catch(e) {
    hideTyping();
    addMsg('bot', '⚠ Cannot reach server. Make sure uvicorn is running on port 8000.');
  }

  btn.disabled = false; inp.focus();
}