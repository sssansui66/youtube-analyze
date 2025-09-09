async function analyze() {
  const url = document.getElementById('url').value.trim();
  const err = document.getElementById('error');
  const resBox = document.getElementById('result');
  const kv = document.getElementById('kv');
  const clip = document.getElementById('clip');
  const source = document.getElementById('source');
  err.style.display = 'none';
  resBox.style.display = 'none';
  if (!url) {
    err.textContent = '请先粘贴一个链接';
    err.style.display = 'block';
    return;
  }
  try {
    const resp = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url })
    });
    const ct = resp.headers.get('content-type') || '';
    let data;
    if (ct.includes('application/json')) {
      try {
        data = await resp.json();
      } catch (err) {
        throw new Error(`[${resp.status}] JSON解析失败: ${String(err)}`);
      }
    } else {
      const text = await resp.text();
      throw new Error(`[${resp.status}] 非JSON响应: ${text.slice(0, 120)}`);
    }
    if (!resp.ok || !data?.ok) throw new Error((data && data.error) || `请求失败(${resp.status})`);

    const m = data.data || {};
    const rows = [
      ['链接', m.url],
      ['发布时间', m.publishedDate || m.publishedAt],
      ['标题', m.title],
      ['描述', m.description],
      ['点赞数', m.likeCount],
      ['观看次数', m.viewCount],
      ['时长', m.durationText || m.durationSeconds],
    ];
    kv.innerHTML = rows.map(([k, v]) => (
      `<div class="label">${k}</div><div>${(v ?? '').toString().replaceAll('\n','<br>')}</div>`
    )).join('');

    clip.value = data.text || '';
    source.textContent = `数据来源: ${m.source || 'unknown'}`;
    resBox.style.display = 'block';
  } catch (e) {
    err.textContent = e.message || String(e);
    err.style.display = 'block';
  }
}

function hook() {
  document.getElementById('analyze').addEventListener('click', analyze);
  document.getElementById('url').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') analyze();
  });
  document.getElementById('copy').addEventListener('click', async () => {
    const txt = document.getElementById('clip').value;
    try { await navigator.clipboard.writeText(txt); } catch {}
  });
}

document.addEventListener('DOMContentLoaded', hook);
