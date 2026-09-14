// CampusJob-Agent 全局通用 API 客户端与导航注入控制器
const API_BASE = '/api/v1';

window.CampusAPI = {
  async get(url) {
    const res = await fetch(`${API_BASE}${url}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  },

  async post(url, data) {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  },

  async put(url, data) {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  },

  async patch(url, data) {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data || {})
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    return await res.json();
  }
};

// 统一 Toast 提示工具
window.showGlobalToast = function(msg, icon = 'check_circle') {
  let toast = document.getElementById('global-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'global-toast';
    toast.className = 'fixed bottom-6 right-6 bg-slate-900 text-white px-4 py-2.5 rounded-lg text-xs font-medium shadow-lg flex items-center gap-2 transform transition-all duration-300 z-50 translate-y-20 opacity-0 pointer-events-none';
    document.body.appendChild(toast);
  }
  toast.innerHTML = `<span class="material-symbols-outlined text-[18px] text-emerald-400">${icon}</span><span>${msg}</span>`;
  toast.classList.remove('translate-y-20', 'opacity-0', 'pointer-events-none');
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0', 'pointer-events-none');
  }, 2800);
};

// 页面加载完成后，标准化顶部导航超链接，确保 6 大页面任意跳转
document.addEventListener('DOMContentLoaded', () => {
  const links = document.querySelectorAll('header a, aside a');
  links.forEach(a => {
    const text = a.textContent || '';
    const href = a.getAttribute('href') || '';
    if (text.includes('仪表盘') || href.includes('dashboard')) {
      a.setAttribute('href', '/dashboard.html');
    } else if (text.includes('看板') || href.includes('jobs')) {
      a.setAttribute('href', '/jobs.html');
    } else if (text.includes('日历') || href.includes('calendar')) {
      a.setAttribute('href', '/calendar.html');
    } else if (text.includes('追踪') || href.includes('tracker')) {
      a.setAttribute('href', '/tracker.html');
    } else if (text.includes('AI') || href.includes('advisory')) {
      a.setAttribute('href', '/advisory.html');
    } else if (text.includes('设置') || href.includes('settings')) {
      a.setAttribute('href', '/settings.html');
    }
  });
});
