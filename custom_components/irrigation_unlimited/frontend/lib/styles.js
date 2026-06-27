/**
 * CSS styles for the panel's Shadow DOM.
 */
export const STYLES = `
:host { display: block; height: 100%; }

/* ── Running indicator (zone active) ──────────────────────────────────────── */
.run-dot {
  display:none; width:8px; height:8px; border-radius:50%;
  background:var(--success-color,#4caf50); margin-right:2px; flex-shrink:0;
  box-shadow:0 0 0 0 rgba(76,175,80,0.6);
  animation: iu-pulse 1.6s ease-out infinite;
}
.sch.running { background:rgba(76,175,80,0.10) !important; }
.sch.running .run-dot { display:inline-block; }
@keyframes iu-pulse {
  0%   { box-shadow:0 0 0 0 rgba(76,175,80,0.55); }
  70%  { box-shadow:0 0 0 6px rgba(76,175,80,0); }
  100% { box-shadow:0 0 0 0 rgba(76,175,80,0); }
}
.wrap { min-height:100%; padding:16px; background:var(--primary-background-color,#f0f2f5);
        font-family:var(--paper-font-body1_-_font-family,Roboto,sans-serif);
        color:var(--primary-text-color,#1a1a1a); box-sizing:border-box; }
.toolbar { display:flex; align-items:center; justify-content:space-between;
           padding:12px 18px; margin-bottom:16px; background:var(--card-background-color,#fff);
           border-radius:14px; box-shadow:var(--ha-card-box-shadow,0 2px 8px rgba(0,0,0,.07)); }
.brand { font-size:1.15rem; font-weight:600; color:var(--primary-color,#1976d2); }
.tbr { display:flex; gap:8px; }
.btn { padding:7px 16px; border-radius:8px; border:none; cursor:pointer;
       font-size:.875rem; font-family:inherit; font-weight:500; transition:filter .15s; }
.bpri { background:var(--primary-color,#1976d2); color:#fff; }
.bpri:hover { filter:brightness(1.1); }
.btxt { background:transparent; color:var(--primary-color,#1976d2); text-decoration:none; display:inline-flex; align-items:center; }
.btxt:hover { background:var(--primary-color-light,#e3f2fd); border-radius:8px; }
.bsm { padding:4px 12px; font-size:.8rem; background:var(--primary-color,#1976d2); color:#fff; border-radius:6px; border:none; cursor:pointer; }
.bsm:hover,.bxs:hover { filter:brightness(1.1); }
.bxs { padding:2px 8px; font-size:.75rem; background:var(--primary-color,#1976d2); color:#fff; border-radius:4px; border:none; cursor:pointer; }
.sm-btn { padding:4px 10px; font-size:.78rem; }
.ib { width:30px; height:30px; border:none; background:none; cursor:pointer; border-radius:6px;
      font-size:14px; display:inline-flex; align-items:center; justify-content:center; transition:background .15s; text-decoration:none; }
.ib:hover { background:var(--secondary-background-color,#f0f0f0); }
.ib.rd:hover { background:#ffebee; }
.ib.sm { width:24px; height:24px; font-size:12px; }
.card { background:var(--card-background-color,#fff); border-radius:12px; margin-bottom:12px; overflow:hidden;
        box-shadow:var(--ha-card-box-shadow,0 2px 8px rgba(0,0,0,.07)); }
.ch { display:flex; align-items:center; gap:8px; padding:14px 16px; cursor:pointer; user-select:none; transition:background .15s; }
.ch:hover { background:var(--secondary-background-color,#f8f8f8); }
.cb { padding:8px 16px 16px; border-top:1px solid var(--divider-color,#e8e8e8); }
.sc { background:var(--secondary-background-color,#f8f9fa); border-radius:8px; margin-bottom:8px;
      overflow:hidden; border:1px solid var(--divider-color,#e8e8e8); }
.sch { display:flex; align-items:center; gap:8px; padding:10px 12px; cursor:pointer; user-select:none; transition:background .15s; }
.sch:hover { background:var(--divider-color,#e8e8e8); }
.scb { padding:8px 12px 12px; border-top:1px solid var(--divider-color,#e0e0e0); }
.chev { font-size:14px; color:var(--secondary-text-color,#888); transition:transform .2s; display:inline-block; width:14px; }
.chev.op { transform:rotate(90deg); }
.ci { font-size:16px; } .cn { font-weight:500; flex:1; }
.cm { font-size:.78rem; color:var(--secondary-text-color,#888); white-space:nowrap; }
.ia { display:flex; gap:2px; margin-left:auto; }
.bdg { font-size:.7rem; padding:2px 6px; border-radius:10px; background:#e0e0e0; color:#555; }
.bdg.off { background:#fff3e0; color:#e65100; }
.chips { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
.chip { font-size:.75rem; padding:3px 9px; border-radius:12px; background:var(--primary-color-light,#e3f2fd); color:var(--primary-color,#1565c0); }
.sh { display:flex; align-items:center; justify-content:space-between; margin:12px 0 6px; }
.st { font-size:.8rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:var(--secondary-text-color,#777); }
.ssh { display:flex; align-items:center; justify-content:space-between; margin:8px 0 4px;
       font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:var(--secondary-text-color,#999); }
.lst { display:flex; flex-direction:column; gap:3px; }
.li { display:flex; align-items:center; gap:7px; padding:5px 8px; border-radius:6px; font-size:.83rem;
      background:var(--card-background-color,#fff); border:1px solid var(--divider-color,#eee); }
.lico { font-size:13px; } .ln { font-weight:500; flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.ld { color:var(--secondary-text-color,#888); white-space:nowrap; font-size:.8rem; }
.ld.mu { opacity:.65; } .la { display:flex; gap:2px; margin-left:auto; }
.empty { text-align:center; padding:48px 24px; color:var(--secondary-text-color,#888); }
.eicon { font-size:48px; margin-bottom:12px; }
.ei { padding:6px 4px; font-size:.8rem; color:var(--secondary-text-color,#999); font-style:italic; margin:4px 0; }
.ei.sm { padding:3px 2px; font-size:.75rem; }
.state { text-align:center; padding:64px; color:var(--secondary-text-color,#888); font-size:1.1rem; }
.state.err { color:var(--error-color,#c62828); }
.ctrl-yaml-row { margin-top:12px; padding-top:10px; border-top:1px solid var(--divider-color,#e8e8e8); }
.ov { position:fixed; inset:0; background:rgba(0,0,0,.5); z-index:9999; display:flex;
      align-items:center; justify-content:center; padding:16px; }
.modal { background:var(--card-background-color,#fff); border-radius:16px; width:100%; max-width:520px;
         max-height:92vh; display:flex; flex-direction:column; box-shadow:0 12px 40px rgba(0,0,0,.25); }
.mh { display:flex; align-items:center; justify-content:space-between; padding:16px 20px;
      border-bottom:1px solid var(--divider-color,#e0e0e0); }
.mt { font-size:1.05rem; font-weight:600; }
.mc { background:none; border:none; cursor:pointer; font-size:18px; color:var(--secondary-text-color,#888); padding:4px 6px; border-radius:4px; }
.mc:hover { background:var(--secondary-background-color,#f0f0f0); }
.mb { overflow-y:auto; padding:16px 20px; flex:1; }
.mf { display:flex; justify-content:flex-end; gap:8px; padding:12px 20px; border-top:1px solid var(--divider-color,#e0e0e0); }
.form { display:flex; flex-direction:column; gap:14px; }
.fg { display:flex; flex-direction:column; gap:4px; }
.fl { font-size:.78rem; font-weight:600; color:var(--secondary-text-color,#777); text-transform:uppercase; letter-spacing:.04em; }
.fi { padding:8px 10px; border:1.5px solid var(--divider-color,#d0d0d0); border-radius:8px;
      font-size:.9rem; font-family:inherit; background:var(--primary-background-color,#fff);
      color:var(--primary-text-color); outline:none; transition:border-color .15s;
      width:100%; box-sizing:border-box; }
.fi:focus { border-color:var(--primary-color,#1976d2); }
.fsec { font-size:.75rem; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
        color:var(--secondary-text-color,#888); margin-top:4px; padding-top:10px;
        border-top:1px solid var(--divider-color,#e8e8e8); }
.tw { display:flex; align-items:center; justify-content:space-between; }
.tl { font-size:.9rem; }
.tg { position:relative; width:44px; height:24px; display:inline-block; }
.ti { opacity:0; width:0; height:0; position:absolute; }
.ts { position:absolute; inset:0; background:#ccc; border-radius:24px; cursor:pointer; transition:background .2s; }
.ts:before { content:""; position:absolute; width:18px; height:18px; top:3px; left:3px; background:#fff;
             border-radius:50%; transition:transform .2s; box-shadow:0 1px 3px rgba(0,0,0,.25); }
.ti:checked+.ts { background:var(--primary-color,#1976d2); }
.ti:checked+.ts:before { transform:translateX(20px); }
.pg { display:flex; flex-wrap:wrap; gap:6px; }
.pill { padding:4px 11px; border-radius:14px; border:1.5px solid var(--divider-color,#ccc);
        font-size:.78rem; cursor:pointer; user-select:none; transition:all .15s; color:var(--secondary-text-color,#666); }
.pill.on { background:var(--primary-color,#1976d2); border-color:var(--primary-color,#1976d2); color:#fff; }
.epw { position:relative; width:100%; }
.val-err  { color:var(--error-color,#db4437); font-size:.8rem;
            padding:6px 0 2px; white-space:pre-line; }
.val-err:empty  { display:none; }
.val-warn { color:var(--warning-color,#f4b400); font-size:.8rem;
            padding:2px 0 2px; white-space:pre-line; }
.val-warn:empty { display:none; }
.bdanger { background:var(--error-color,#db4437)!important; color:#fff!important; }
.bdanger:hover { opacity:.85; }
.fg-title { font-size:.72rem; font-weight:600; color:var(--secondary-text-color,#888);
            text-transform:uppercase; letter-spacing:.06em;
            margin:12px 0 4px; padding-top:8px;
            border-top:1px solid var(--divider-color,#e0e0e0); }
.ep-dd {
  position:absolute; top:100%; left:0; right:0; z-index:9000;
  background:var(--card-background-color,#fff);
  border:1.5px solid var(--primary-color,#1976d2); border-top:none;
  border-radius:0 0 8px 8px; max-height:220px; overflow-y:auto;
  box-shadow:0 6px 16px rgba(0,0,0,.18);
}
.ep-item { padding:7px 12px; cursor:pointer; display:flex; flex-direction:column; gap:1px; }
.ep-item:hover { background:var(--secondary-background-color,#f0f0f0); }
.ep-id { font-size:.83rem; font-weight:500; }
.ep-name { font-size:.72rem; color:var(--secondary-text-color,#888); }
.yp { background:#1e1e1e; color:#d4d4d4; padding:14px; border-radius:8px; font-family:monospace;
      font-size:.78rem; white-space:pre; overflow:auto; max-height:60vh; margin:0; }
`;
