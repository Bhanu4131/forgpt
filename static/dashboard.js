async function refreshState() {
        try {
          const r = await fetch('/api/state');
          const s = await r.json();
          const p = (v) => (v === null || v === undefined) ? "—" : v;

          document.getElementById('in_trade').className = 'pill ' + (s.in_trade ? 'ok' : 'bad');
          document.getElementById('in_trade').textContent = s.in_trade ? 'Yes' : 'No';

          document.getElementById('entry').textContent = p(s.entry);
          document.getElementById('sl').textContent = p(s.sl);
          document.getElementById('target').textContent = p(s.target);
          document.getElementById('order_id').textContent = p(s.order_id);
          document.getElementById('sl_trailed').className = 'pill ' + (s.sl_trailed ? 'ok' : '');
          document.getElementById('sl_trailed').textContent = s.sl_trailed ? 'True' : 'False';

          document.getElementById('socket_status').textContent = s.socket_up ? 'UP' : 'DOWN';
          document.getElementById('socket_status').className = 'pill ' + (s.socket_up ? 'ok' : 'bad');
        } catch (e) {
          console.error(e);
        }
      }

      document.getElementById('updateForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const sl = document.getElementById('new_sl').value;
        const target = document.getElementById('new_target').value;

        const payload = {};
        if (sl) payload.sl = parseFloat(sl);
        if (target) payload.target = parseFloat(target);

        const r = await fetch('/api/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const out = await r.json();
        alert(out.message || 'Updated');
        document.getElementById('new_sl').value = '';
        document.getElementById('new_target').value = '';
        refreshState();
      });

      document.getElementById('trailBtn').addEventListener('click', async () => {
        const r = await fetch('/api/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trail_to_entry: true })
        });
        const out = await r.json();
        alert(out.message || 'Trailed SL to entry');
        refreshState();
      });

      document.getElementById('exitBtn').addEventListener('click', async () => {
        if (!confirm('Exit trade now?')) return;
        const r = await fetch('/api/exit', { method: 'POST' });
        const out = await r.json();
        alert(out.message || 'Exit requested');
        refreshState();
      });

      refreshState();
      setInterval(refreshState, 2000);