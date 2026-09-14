// 全局伴随式求职 Agent 参谋抽屉 (Omni-Agent Drawer)
// 支持在任何页面通过快捷键 Cmd+J / Ctrl+J 或点击右下角浮标随时唤起
// 支持在职位详情抽屉中伴随推出（折纸展开效果 + 独立会话上下文隔离）
(function() {
  // 按照不同业务上下文隔离对话记录：例如 'global', 'job_huawei', 'job_zhejiang-fgw', 'job_1' 等
  const contextChatStore = {};
  let activeContextKey = 'global';
  let activeJobMeta = null;

  function injectOrigamiStyles() {
    if (document.getElementById('omni-origami-styles')) return;
    const styleEl = document.createElement('style');
    styleEl.id = 'omni-origami-styles';
    styleEl.textContent = `
      @keyframes omniOrigamiUnfold {
        0% {
          opacity: 0;
          transform: perspective(1400px) rotateY(-50deg) translateX(40px) scale(0.96);
        }
        60% {
          opacity: 0.95;
          transform: perspective(1400px) rotateY(6deg) translateX(-4px) scale(1.01);
        }
        100% {
          opacity: 1;
          transform: perspective(1400px) rotateY(0deg) translateX(0) scale(1);
        }
      }

      @keyframes omniOrigamiFold {
        0% {
          opacity: 1;
          transform: perspective(1400px) rotateY(0deg) translateX(0) scale(1);
        }
        100% {
          opacity: 0;
          transform: perspective(1400px) rotateY(-45deg) translateX(50px) scale(0.95);
        }
      }

      #omni-agent-drawer-panel.origami-unfolding {
        animation: omniOrigamiUnfold 0.42s cubic-bezier(0.16, 1, 0.3, 1) forwards !important;
        transform-origin: left center !important;
        box-shadow: -20px 0 45px -5px rgba(15, 23, 42, 0.22), -3px 0 12px rgba(15, 23, 42, 0.1) !important;
      }

      #omni-agent-drawer-panel.origami-folding {
        animation: omniOrigamiFold 0.25s cubic-bezier(0.4, 0, 1, 1) forwards !important;
        transform-origin: left center !important;
      }

      /* 伴随模式：去掉全屏黑遮罩，只显示右侧 Agent 面板，点击左侧职位卡片依然清晰 */
      #omni-agent-drawer-container.job-companion-mode {
        background: transparent !important;
        backdrop-filter: none !important;
        pointer-events: none;
      }

      #omni-agent-drawer-container.job-companion-mode #omni-agent-drawer-panel {
        pointer-events: auto;
        border-left: 2px solid rgba(251, 191, 36, 0.4);
      }
    `;
    document.head.appendChild(styleEl);
  }

  function injectOmniAgentDrawer() {
    if (document.getElementById('omni-agent-drawer-container')) return;
    injectOrigamiStyles();

    // 1. 浮动触发胶囊 (右下角常驻，带呼吸微光)
    const floatBtn = document.createElement('div');
    floatBtn.id = 'omni-agent-float-trigger';
    floatBtn.className = 'fixed bottom-6 right-6 z-40 flex items-center gap-2 px-3 py-2 bg-slate-900/90 hover:bg-slate-950 text-white rounded-full shadow-lg border border-amber-400/40 backdrop-blur-md cursor-pointer transition-all hover:scale-105 active:scale-95 group select-none';
    floatBtn.innerHTML = `
      <div class="w-6 h-6 rounded-full bg-amber-400 text-slate-950 flex items-center justify-center font-bold text-xs shadow-xs">
        <span class="material-symbols-outlined text-[15px]">smart_toy</span>
      </div>
      <span class="text-xs font-bold text-slate-100 group-hover:text-amber-300 transition-colors">求职 Agent 参谋</span>
      <span class="px-1.5 py-0.2 bg-white/10 text-slate-300 text-[10px] font-mono rounded border border-white/15">⌘J</span>
    `;
    floatBtn.onclick = () => toggleOmniDrawer();
    document.body.appendChild(floatBtn);

    // 2. 抽屉本体与背景遮罩
    const drawerContainer = document.createElement('div');
    drawerContainer.id = 'omni-agent-drawer-container';
    drawerContainer.className = 'hidden fixed inset-0 z-50 bg-slate-950/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-150';
    drawerContainer.innerHTML = `
      <div id="omni-agent-drawer-panel" class="w-full max-w-md md:max-w-[440px] bg-white h-full shadow-2xl border-l border-slate-200 flex flex-col transform transition-transform duration-200 translate-x-full">
        <!-- 头部 Header -->
        <div class="px-5 py-3.5 border-b border-slate-200 flex items-center justify-between bg-slate-50/80 backdrop-blur-sm">
          <div class="flex items-center gap-2.5">
            <div class="w-7 h-7 rounded-lg bg-amber-400 text-slate-950 flex items-center justify-center font-bold shadow-xs">
              <span class="material-symbols-outlined text-[17px]">smart_toy</span>
            </div>
            <div>
              <div class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                CampusJob 随身参谋
                <span id="omni-status-tag" class="px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 text-[10px] font-mono font-bold border border-emerald-200">在线</span>
              </div>
              <div id="omni-page-context-pill" class="text-[10px] font-mono text-slate-500 mt-0.5 flex items-center gap-1">
                <span class="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse"></span>
                <span>当前上下文: 探索中...</span>
              </div>
            </div>
          </div>
          <div class="flex items-center gap-1.5">
            <button onclick="clearOmniChat()" class="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100 transition-colors text-xs flex items-center" title="清空当前岗位对话记录">
              <span class="material-symbols-outlined text-[17px]">delete_sweep</span>
            </button>
            <button onclick="toggleOmniDrawer()" class="text-slate-400 hover:text-slate-700 p-1.5 rounded-md hover:bg-slate-100 transition-colors text-xs flex items-center" title="关闭 (Esc)">
              <span class="material-symbols-outlined text-[18px]">close</span>
            </button>
          </div>
        </div>

        <!-- 快捷场景推荐条 -->
        <div class="px-4 py-2 bg-slate-100/70 border-b border-slate-200 flex items-center gap-2 overflow-x-auto text-[11px] font-mono no-scrollbar" id="omni-quick-chips">
          <button onclick="triggerOmniQuickAction('诊断当前页面焦点与建议')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            🎯 诊断本页战备重点
          </button>
          <button onclick="triggerOmniQuickAction('针对明天的阿里二面，帮我生成3道核心追问')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            💡 阿里二面押题
          </button>
          <button onclick="triggerOmniQuickAction('帮我生成一份礼貌顺延大厂三方的HR沟通邮件')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            ✉️ 延期三方话术
          </button>
        </div>

        <!-- 消息对话体 Message History -->
        <div id="omni-chat-body" class="flex-1 overflow-y-auto p-4 space-y-3.5 bg-slate-50/40 text-xs leading-relaxed">
          <!-- 默认迎宾提示由 switchContextTo 动态填充，初始不包含任何累积历史 -->
        </div>

        <!-- 输入区域 Input Footer -->
        <div class="p-3.5 border-t border-slate-200 bg-white">
          <form id="omni-chat-form" onsubmit="handleOmniChatSubmit(event)" class="space-y-2">
            <div class="relative">
              <textarea id="omni-chat-input" rows="2" placeholder="问我关于此岗位匹配度、STAR亮点击破或避坑红线... (Enter 发送, Shift+Enter 换行)" class="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 focus:border-amber-400 focus:bg-white rounded-xl p-2.5 pr-10 text-xs text-slate-800 placeholder:text-slate-400 focus:outline-none transition-all resize-none leading-relaxed"></textarea>
              <button type="submit" class="absolute right-2 bottom-3 w-7 h-7 bg-amber-400 hover:bg-amber-500 text-slate-950 rounded-lg flex items-center justify-center font-bold shadow-2xs transition-all active:scale-95 cursor-pointer">
                <span class="material-symbols-outlined text-[16px]">send</span>
              </button>
            </div>
            <div class="flex items-center justify-between text-[11px] font-mono text-slate-400 px-0.5">
              <span id="omni-status-indicator">就绪 · 独立岗位沙箱已挂载</span>
              <span>按 Esc 退出</span>
            </div>
          </form>
        </div>
      </div>
    `;

    drawerContainer.onclick = function(e) {
      if (e.target === drawerContainer) {
        toggleOmniDrawer();
      }
    };

    document.body.appendChild(drawerContainer);

    // 绑定回车发送事件
    const inputEl = document.getElementById('omni-chat-input');
    if (inputEl) {
      inputEl.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          handleOmniChatSubmit(e);
        }
      });
    }

    injectGlobalReasoningHUD();
  }

  // 全局推理透出 HUD
  function injectGlobalReasoningHUD() {
    if (document.getElementById('global-score-reasoning-modal')) return;
    const hud = document.createElement('div');
    hud.id = 'global-score-reasoning-modal';
    hud.className = 'hidden fixed inset-0 z-[999] bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-150';
    hud.onclick = function(e) {
      if (e.target === hud) closeGlobalScoreReasoningHUD();
    };
    hud.innerHTML = `
      <div class="bg-white border border-slate-200 rounded-xl max-w-md w-full p-5 shadow-2xl space-y-4" onclick="event.stopPropagation()">
        <div class="flex items-center justify-between border-b border-slate-100 pb-3">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-amber-500 text-[20px]">psychology</span>
            <div>
              <h4 class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
                <span id="global-hud-target-name">目标岗位</span>
                <span class="text-[10px] font-mono px-1.5 py-0.2 bg-amber-100 text-amber-900 rounded font-bold">推演拆解</span>
              </h4>
              <span class="text-[10px] font-mono text-slate-500">基于工学硕士+党员脱敏画像精算</span>
            </div>
          </div>
          <button onclick="closeGlobalScoreReasoningHUD()" class="text-slate-400 hover:text-slate-600">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div class="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
          <span class="text-xs text-slate-600 font-medium">契合度综合评分</span>
          <span id="global-hud-score-value" class="text-2xl font-black font-mono text-emerald-700">92分</span>
        </div>

        <div class="space-y-2">
          <div class="text-[11px] font-bold text-slate-700 flex items-center gap-1">
            <span class="material-symbols-outlined text-[14px] text-amber-600">tune</span>
            评分模型拆解因子 (Reasoning Trace):
          </div>
          <div id="global-hud-factors-list" class="space-y-1.5 font-mono text-[11px]"></div>
        </div>

        <div class="pt-2 border-t border-slate-100 flex justify-end">
          <button onclick="closeGlobalScoreReasoningHUD()" class="px-3.5 py-1.5 bg-amber-400 hover:bg-amber-500 text-slate-950 text-xs font-bold rounded-lg shadow-2xs">
            完全理解
          </button>
        </div>
      </div>
    `;
    document.body.appendChild(hud);
  }

  window.showGlobalScoreReasoningHUD = function(targetName, scoreValue, factors) {
    const modal = document.getElementById('global-score-reasoning-modal');
    const nameEl = document.getElementById('global-hud-target-name');
    const valEl = document.getElementById('global-hud-score-value');
    const listEl = document.getElementById('global-hud-factors-list');

    if (nameEl) nameEl.textContent = targetName;
    if (valEl) valEl.textContent = `${scoreValue}分`;
    if (listEl) {
      listEl.innerHTML = factors.map(f => {
        const isNegative = f.includes('-');
        return `
          <div class="flex items-center justify-between p-2 rounded ${isNegative ? 'bg-rose-50 text-rose-800 border border-rose-200' : 'bg-emerald-50 text-emerald-800 border border-emerald-200'}">
            <span>${f.split(' ')[0]}</span>
            <span class="font-bold">${f.split(' ')[1] || ''}</span>
          </div>
        `;
      }).join('');
    }

    if (modal) modal.classList.remove('hidden');
  };

  window.closeGlobalScoreReasoningHUD = function() {
    const modal = document.getElementById('global-score-reasoning-modal');
    if (modal) modal.classList.add('hidden');
  };

  function getPageContext() {
    const path = window.location.pathname;
    let label = '全局总览';
    let entity = '';

    if (activeJobMeta) {
      label = activeJobMeta.company ? `${activeJobMeta.company} · ${activeJobMeta.title}` : activeJobMeta.title;
      entity = `岗位上下文 [${activeJobMeta.id}]`;
    } else if (path.includes('jobs')) {
      label = '校招雷达 (/jobs)';
      const activeCard = document.querySelector('.job-card.active, .job-item.selected') || document.querySelector('h3.font-bold');
      if (activeCard) entity = activeCard.innerText.split('\n')[0].trim();
    } else if (path.includes('calendar')) {
      label = '日历日程 (/calendar)';
      entity = '9月15日冲突与临考备战包';
    } else if (path.includes('tracker')) {
      label = '投递看板 (/tracker)';
      entity = '18项求职进度';
    } else if (path.includes('advisory')) {
      label = 'AI 顾问诊断 (/advisory)';
      entity = 'Offer 决策沙盒推演';
    } else if (path.includes('settings')) {
      label = '控制中心 (/settings)';
    }

    return { path, label, entity };
  }

  // 根据上下文生成初始迎宾卡片
  function createInitialGreetingHTML(contextKey, jobMeta) {
    if (jobMeta) {
      const isCivil = jobMeta.category === 'civil' || (jobMeta.categoryBadge && jobMeta.categoryBadge.includes('考公'));
      return `
        <div class="flex justify-start">
          <div class="bg-white text-slate-800 p-3.5 rounded-xl border border-amber-200/80 shadow-2xs max-w-[94%] space-y-2">
            <div class="flex items-center justify-between border-b border-amber-100 pb-1.5">
              <span class="font-bold text-amber-800 flex items-center gap-1">
                <span class="material-symbols-outlined text-[15px] text-amber-500">psychology</span>
                【${escapeHtml(jobMeta.company)}】专项参谋
              </span>
              <span class="text-[10px] font-mono px-1.5 py-0.2 bg-amber-100 text-amber-900 rounded font-bold">
                ${escapeHtml(jobMeta.matchScore || '匹配度评估')}
              </span>
            </div>
            <p class="text-slate-600 font-sans leading-relaxed text-[11px]">
              你好！针对【${escapeHtml(jobMeta.title)}】，我已单独为你建立<strong>独立咨询沙盒</strong>。
              ${isCivil
                ? '已为你调取往年进面线与申论热点，可随时问我报考门槛、竞争比与复习重点。'
                : '已根据你的工学硕士技术背景建立面试对齐模型，可随时问我 STAR 自述亮点、避坑红线或技术追问押题。'}
            </p>
            <div class="text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-100 flex items-center justify-between">
              <span>当前上下文已锁定岗位</span>
              <span class="text-emerald-700 font-bold">● 独立沙箱隔离</span>
            </div>
          </div>
        </div>
      `;
    }

    return `
      <div class="flex justify-start">
        <div class="bg-white text-slate-800 p-3 rounded-xl border border-slate-200 shadow-2xs max-w-[92%] space-y-2">
          <div class="font-bold text-amber-800 flex items-center gap-1.5">
            <span class="material-symbols-outlined text-[16px]">psychology</span>
            你好！我是你的专属求职参谋
          </div>
          <p class="text-slate-600 font-sans leading-relaxed">
            我已结合你的【计算机工学硕士 · 中共党员】画像就绪。无论你在浏览岗位、查看日历还是推进看板，我都能随时为你提供匹配诊断、考公测算与面试避坑策略。
          </p>
          <div class="text-[10px] text-slate-400 font-mono pt-1 border-t border-slate-100 flex items-center justify-between">
            <span>支持快捷键 Cmd+J 呼出/隐藏</span>
            <span class="text-emerald-700 font-bold">● 本地沙箱脱敏保护中</span>
          </div>
        </div>
      </div>
    `;
  }

  // 动态根据岗位定制快捷推荐按钮
  function updateQuickChipsForContext(jobMeta) {
    const chipsContainer = document.getElementById('omni-quick-chips');
    if (!chipsContainer) return;

    if (jobMeta) {
      const isCivil = jobMeta.category === 'civil' || (jobMeta.categoryBadge && jobMeta.categoryBadge.includes('考公'));
      if (isCivil) {
        chipsContainer.innerHTML = `
          <button onclick="triggerOmniQuickAction('针对本岗位的专业代码与党员要求，排查硬性资格门槛')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            📋 资格五重核验
          </button>
          <button onclick="triggerOmniQuickAction('历年进面线与报录竞争比预估，以及本岗位申论专项考点')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            📊 进面分与考点
          </button>
          <button onclick="triggerOmniQuickAction('针对本岗位在基层服务期与政审维度的避坑注意事项')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            ⚠️ 避坑红线
          </button>
        `;
      } else {
        chipsContainer.innerHTML = `
          <button onclick="triggerOmniQuickAction('结合我的脱敏画像，生成针对该岗位的定制化 STAR 面试自述亮点')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            🌟 定制 STAR 亮点
          </button>
          <button onclick="triggerOmniQuickAction('生成该岗位最常考的3道高频技术面试题与标准回答框架')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            💡 核心技术押题
          </button>
          <button onclick="triggerOmniQuickAction('面试官最可能追问的经历软肋与避坑对策')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
            🛡️ 避坑抗辩对策
          </button>
        `;
      }
    } else {
      chipsContainer.innerHTML = `
        <button onclick="triggerOmniQuickAction('诊断当前页面焦点与建议')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
          🎯 诊断本页战备重点
        </button>
        <button onclick="triggerOmniQuickAction('针对明天的阿里二面，帮我生成3道核心追问')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
          💡 阿里二面押题
        </button>
        <button onclick="triggerOmniQuickAction('帮我生成一份礼貌顺延大厂三方的HR沟通邮件')" class="px-2.5 py-1 bg-white hover:bg-amber-50 text-slate-700 hover:text-amber-800 border border-slate-200 hover:border-amber-300 rounded-full transition-colors shrink-0 shadow-2xs">
          ✉️ 延期三方话术
        </button>
      `;
    }
  }

  // 切换会话上下文：每个岗位一个独立的聊天历史沙盒
  function switchContextTo(contextKey, jobMeta = null) {
    activeContextKey = contextKey || 'global';
    activeJobMeta = jobMeta;

    const chatBody = document.getElementById('omni-chat-body');
    const pill = document.getElementById('omni-page-context-pill');

    // 若此前没有此上下文的历史，则初始化为空数组，并渲染初始卡片
    if (!contextChatStore[activeContextKey]) {
      contextChatStore[activeContextKey] = [];
    }

    if (chatBody) {
      chatBody.innerHTML = '';
      const initialGreeting = createInitialGreetingHTML(activeContextKey, activeJobMeta);
      chatBody.innerHTML = initialGreeting;

      // 回放该上下文的历史消息（若有）
      const history = contextChatStore[activeContextKey];
      history.forEach(item => {
        if (item.type === 'user') {
          const userBubble = document.createElement('div');
          userBubble.className = 'flex justify-end';
          userBubble.innerHTML = `
            <div class="bg-amber-100 text-amber-950 p-2.5 rounded-xl max-w-[85%] font-sans text-xs leading-relaxed font-medium shadow-2xs border border-amber-200">
              ${escapeHtml(item.text)}
            </div>
          `;
          chatBody.appendChild(userBubble);
        } else if (item.type === 'agent') {
          const replyBubble = document.createElement('div');
          replyBubble.className = 'flex justify-start';
          replyBubble.innerHTML = `
            <div class="bg-white text-slate-800 p-3.5 rounded-xl border border-slate-200 shadow-2xs max-w-[92%] space-y-2">
              <div class="flex items-center justify-between border-b border-slate-100 pb-1.5 mb-1">
                <span class="font-bold text-amber-800 flex items-center gap-1">
                  <span class="material-symbols-outlined text-[15px]">psychology</span>
                  参谋诊断结果
                </span>
                <span class="text-[10px] font-mono text-slate-400">${item.time || ''}</span>
              </div>
              <div class="text-slate-700 font-sans leading-relaxed whitespace-pre-wrap">${escapeHtml(item.text)}</div>
              ${item.actions && item.actions.length ? `
                <div class="pt-2 border-t border-slate-100 space-y-1">
                  ${item.actions.map(act => `
                    <button type="button" onclick="handleOmniActionClick('${escapeHtml(act)}')" class="block w-full text-left text-[11px] font-medium text-amber-800 hover:text-amber-900 hover:bg-amber-50 px-2 py-1 rounded transition-colors">
                      ${escapeHtml(act)}
                    </button>
                  `).join('')}
                </div>
              ` : ''}
            </div>
          `;
          chatBody.appendChild(replyBubble);
        }
      });
      chatBody.scrollTop = chatBody.scrollHeight;
    }

    if (pill) {
      if (jobMeta) {
        pill.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span><span class="font-bold text-slate-700">${escapeHtml(jobMeta.company)} · ${escapeHtml(jobMeta.title)}</span>`;
      } else {
        const ctx = getPageContext();
        pill.innerHTML = `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span><span>在 ${ctx.label} ${ctx.entity ? '· ' + ctx.entity : ''}</span>`;
      }
    }

    updateQuickChipsForContext(jobMeta);
  }

  // 伴随式打开 Agent：配合岗位抽屉向左推移与折纸展开
  window.openJobCompanionAgent = function(jobInfo) {
    injectOmniAgentDrawer();
    const container = document.getElementById('omni-agent-drawer-container');
    const panel = document.getElementById('omni-agent-drawer-panel');
    const jobDrawer = document.getElementById('job-detail-drawer');
    if (!container || !panel) return;

    const contextKey = 'job_' + (jobInfo.id || 'current');
    switchContextTo(contextKey, jobInfo);

    // 1. 将职位详情抽屉往左推
    if (jobDrawer) {
      jobDrawer.classList.add('drawer-pushed-left');
    }

    // 2. 伴随模式样式激活（无全屏黑罩，不阻断左侧职位卡片视线）
    container.classList.add('job-companion-mode');
    container.classList.remove('hidden');

    // 3. 执行折纸推出动画
    panel.classList.remove('translate-x-full');
    panel.classList.remove('origami-folding');
    panel.classList.add('origami-unfolding');

    // 4. 更新职位抽屉底部的“问 Agent”按钮状态
    const agentBtnIcon = document.getElementById('drawer-agent-icon');
    const agentBtnText = document.getElementById('drawer-agent-text');
    if (agentBtnIcon) agentBtnIcon.textContent = 'close';
    if (agentBtnText) agentBtnText.textContent = '收起 Agent';

    setTimeout(() => {
      document.getElementById('omni-chat-input')?.focus();
    }, 200);
  };

  // 关闭伴随式 Agent，并将职位卡片恢复
  window.closeJobCompanionAgent = function() {
    const container = document.getElementById('omni-agent-drawer-container');
    const panel = document.getElementById('omni-agent-drawer-panel');
    const jobDrawer = document.getElementById('job-detail-drawer');

    // 1. 将职位详情卡片复位
    if (jobDrawer) {
      jobDrawer.classList.remove('drawer-pushed-left');
    }

    // 2. 更新底部按钮
    const agentBtnIcon = document.getElementById('drawer-agent-icon');
    const agentBtnText = document.getElementById('drawer-agent-text');
    if (agentBtnIcon) agentBtnIcon.textContent = 'smart_toy';
    if (agentBtnText) agentBtnText.textContent = '问 Agent';

    if (!container || !panel || container.classList.contains('hidden')) return;

    // 3. 执行折叠收拢动画
    panel.classList.remove('origami-unfolding');
    panel.classList.add('origami-folding');

    setTimeout(() => {
      panel.classList.add('translate-x-full');
      panel.classList.remove('origami-folding');
      container.classList.remove('job-companion-mode');
      container.classList.add('hidden');
    }, 220);
  };

  // 切换伴随式 Agent 开关
  window.toggleJobCompanionAgent = function(jobInfo) {
    const container = document.getElementById('omni-agent-drawer-container');
    const isOpen = container && !container.classList.contains('hidden');
    const isSameContext = activeContextKey === ('job_' + (jobInfo.id || 'current'));

    if (isOpen && isSameContext) {
      window.closeJobCompanionAgent();
    } else {
      window.openJobCompanionAgent(jobInfo);
    }
  };

  window.toggleOmniDrawer = function() {
    const container = document.getElementById('omni-agent-drawer-container');
    const panel = document.getElementById('omni-agent-drawer-panel');
    if (!container || !panel) return;

    const isHidden = container.classList.contains('hidden');
    if (isHidden) {
      container.classList.remove('job-companion-mode');
      container.classList.remove('hidden');
      panel.classList.remove('origami-unfolding', 'origami-folding');
      setTimeout(() => {
        panel.classList.remove('translate-x-full');
      }, 10);

      // 全局模式
      switchContextTo('global', null);

      setTimeout(() => {
        document.getElementById('omni-chat-input')?.focus();
      }, 100);
    } else {
      // 若当前处于伴随模式，顺便复位职位抽屉
      const jobDrawer = document.getElementById('job-detail-drawer');
      if (jobDrawer) jobDrawer.classList.remove('drawer-pushed-left');

      const agentBtnIcon = document.getElementById('drawer-agent-icon');
      const agentBtnText = document.getElementById('drawer-agent-text');
      if (agentBtnIcon) agentBtnIcon.textContent = 'smart_toy';
      if (agentBtnText) agentBtnText.textContent = '问 Agent';

      if (container.classList.contains('job-companion-mode')) {
        panel.classList.remove('origami-unfolding');
        panel.classList.add('origami-folding');
        setTimeout(() => {
          panel.classList.add('translate-x-full');
          panel.classList.remove('origami-folding');
          container.classList.remove('job-companion-mode');
          container.classList.add('hidden');
        }, 220);
      } else {
        panel.classList.add('translate-x-full');
        setTimeout(() => {
          container.classList.add('hidden');
        }, 200);
      }
    }
  };

  window.triggerOmniQuickAction = function(promptText) {
    const inputEl = document.getElementById('omni-chat-input');
    if (inputEl) {
      inputEl.value = promptText;
      handleOmniChatSubmit(new Event('submit'));
    }
  };

  window.clearOmniChat = function() {
    // 仅清空当前上下文的对话记录
    contextChatStore[activeContextKey] = [];
    const chatBody = document.getElementById('omni-chat-body');
    if (chatBody) {
      chatBody.innerHTML = createInitialGreetingHTML(activeContextKey, activeJobMeta);
      const clearedNote = document.createElement('div');
      clearedNote.className = 'flex justify-start';
      clearedNote.innerHTML = `
        <div class="bg-white text-slate-600 p-2.5 rounded-xl border border-slate-200 shadow-2xs max-w-[92%] text-[11px] font-mono flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[14px] text-amber-500">check_circle</span>
          <span>当前上下文对话已彻底清空重置，随时向我提问！</span>
        </div>
      `;
      chatBody.appendChild(clearedNote);
    }
  };

  window.handleOmniChatSubmit = async function(e) {
    if (e && e.preventDefault) e.preventDefault();
    const input = document.getElementById('omni-chat-input');
    const msg = input?.value?.trim();
    if (!msg) return;

    input.value = '';
    const chatBody = document.getElementById('omni-chat-body');
    const ctx = getPageContext();

    // 记录用户消息进当前上下文
    if (!contextChatStore[activeContextKey]) {
      contextChatStore[activeContextKey] = [];
    }
    contextChatStore[activeContextKey].push({
      type: 'user',
      text: msg,
      time: new Date().toLocaleTimeString()
    });

    // 渲染用户消息
    const userBubble = document.createElement('div');
    userBubble.className = 'flex justify-end';
    userBubble.innerHTML = `
      <div class="bg-amber-100 text-amber-950 p-2.5 rounded-xl max-w-[85%] font-sans text-xs leading-relaxed font-medium shadow-2xs border border-amber-200">
        ${escapeHtml(msg)}
      </div>
    `;
    chatBody.appendChild(userBubble);
    chatBody.scrollTop = chatBody.scrollHeight;

    // Loading 骨架
    const loadingBubble = document.createElement('div');
    loadingBubble.className = 'flex justify-start';
    loadingBubble.innerHTML = `
      <div class="bg-white text-slate-500 p-2.5 rounded-xl border border-slate-200 shadow-2xs text-xs flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-amber-400 animate-ping"></span>
        <span>Agent 正在针对【${escapeHtml(ctx.label)}】结合脱敏画像推演中...</span>
      </div>
    `;
    chatBody.appendChild(loadingBubble);
    chatBody.scrollTop = chatBody.scrollHeight;

    try {
      const resp = await fetch('/api/v1/advisory/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          context_page: ctx.path,
          context_title: ctx.label
        })
      });

      loadingBubble.remove();

      if (resp.ok) {
        const data = await resp.json();
        const timeStr = new Date().toLocaleTimeString();

        // 存入当前上下文历史
        contextChatStore[activeContextKey].push({
          type: 'agent',
          text: data.reply,
          actions: data.related_actions || [],
          time: timeStr
        });

        const replyBubble = document.createElement('div');
        replyBubble.className = 'flex justify-start';
        replyBubble.innerHTML = `
          <div class="bg-white text-slate-800 p-3.5 rounded-xl border border-slate-200 shadow-2xs max-w-[92%] space-y-2">
            <div class="flex items-center justify-between border-b border-slate-100 pb-1.5 mb-1">
              <span class="font-bold text-amber-800 flex items-center gap-1">
                <span class="material-symbols-outlined text-[15px]">psychology</span>
                参谋诊断结果
              </span>
              <span class="text-[10px] font-mono text-slate-400">${timeStr}</span>
            </div>
            <div class="text-slate-700 font-sans leading-relaxed whitespace-pre-wrap">${escapeHtml(data.reply)}</div>
            ${data.related_actions && data.related_actions.length ? `
              <div class="pt-2 border-t border-slate-100 space-y-1">
                ${data.related_actions.map(act => `
                  <button type="button" onclick="handleOmniActionClick('${escapeHtml(act)}')" class="block w-full text-left text-[11px] font-medium text-amber-800 hover:text-amber-900 hover:bg-amber-50 px-2 py-1 rounded transition-colors">
                    ${escapeHtml(act)}
                  </button>
                `).join('')}
              </div>
            ` : ''}
          </div>
        `;
        chatBody.appendChild(replyBubble);
      } else {
        throw new Error('API 返回异常');
      }
    } catch (err) {
      loadingBubble.remove();
      const errBubble = document.createElement('div');
      errBubble.className = 'flex justify-start';
      errBubble.innerHTML = `
        <div class="bg-rose-50 text-rose-800 p-2.5 rounded-xl border border-rose-200 text-xs">
          抱歉，参谋响应遇到了网络波动，请重试。
        </div>
      `;
      chatBody.appendChild(errBubble);
    }
    chatBody.scrollTop = chatBody.scrollHeight;
  };

  window.handleOmniActionClick = function(actionDesc) {
    if (actionDesc.includes('备忘录') || actionDesc.includes('投递')) {
      if (window.location.pathname.includes('tracker')) {
        showGlobalToast('已将 Agent 建议同步更新至投递备忘录');
      } else {
        showGlobalToast('建议已复制，并同步预置至【投递追踪看板】！');
      }
    } else {
      showGlobalToast(`已触发动作：${actionDesc}`);
    }
  };

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.innerText = text;
    return div.innerHTML;
  }

  function showGlobalToast(msg) {
    const existing = document.getElementById('global-toast-container');
    const container = existing || document.createElement('div');
    if (!existing) {
      container.id = 'global-toast-container';
      container.className = 'fixed bottom-24 right-6 z-[100] flex flex-col gap-2 pointer-events-none';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    toast.className = 'bg-slate-900 text-white px-4 py-2.5 rounded-lg shadow-xl text-xs flex items-center gap-2 pointer-events-auto border border-amber-400/30 animate-in fade-in duration-150';
    toast.innerHTML = `
      <span class="material-symbols-outlined text-amber-400 text-[16px]">check_circle</span>
      <span>${msg}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
  }

  // 监听键盘全局快捷键 Cmd + J / Ctrl + J (Agent 参谋) 与 Cmd + K / Ctrl + K (全局搜索)
  window.addEventListener('keydown', function(e) {
    if ((e.metaKey || e.ctrlKey) && (e.key === 'j' || e.key === 'J')) {
      e.preventDefault();
      toggleOmniDrawer();
    }
    if ((e.metaKey || e.ctrlKey) && (e.key === 'k' || e.key === 'K')) {
      e.preventDefault();
      const localSearchInput = document.getElementById('global-search-input') || document.querySelector('header input[type="text"]');
      if (localSearchInput) {
        localSearchInput.focus();
        localSearchInput.select();
      } else {
        window.location.href = '/jobs';
      }
    }
    if (e.key === 'Escape') {
      const container = document.getElementById('omni-agent-drawer-container');
      if (container && !container.classList.contains('hidden')) {
        toggleOmniDrawer();
      }
    }
  });

  // 绑定全局顶栏搜索框回车快速直达 /jobs
  function bindGlobalHeaderSearch() {
    const inputs = document.querySelectorAll('header input[type="text"]');
    inputs.forEach(input => {
      input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
          e.preventDefault();
          const query = input.value.trim();
          if (query) {
            if (window.location.pathname.includes('jobs')) {
              // 当前就在 jobs，直接调用过滤
              const stateQuery = query.toLowerCase();
              if (window.state) {
                window.state.searchQuery = stateQuery;
                if (typeof window.filterJobs === 'function') window.filterJobs();
              }
            } else {
              window.location.href = `/jobs?q=${encodeURIComponent(query)}`;
            }
          }
        }
      });
    });
  }

  // 全局求职画像顶栏状态动态同步
  async function syncGlobalProfileHeader() {
    try {
      const res = await fetch('/api/v1/profile');
      if (!res.ok) return;
      const data = await res.json();
      const headerDegree = document.getElementById('header-profile-degree');
      const headerMajor = document.getElementById('header-profile-major');

      if (headerDegree) {
        if (data.grad_year && data.education_level) {
          headerDegree.innerText = `${data.grad_year}届 ${data.education_level}`;
        } else if (data.education_level) {
          headerDegree.innerText = data.education_level;
        } else {
          headerDegree.innerText = '个人求职画像';
        }
      }

      if (headerMajor) {
        if (data.major_tags && data.major_tags.length > 0) {
          const firstMajor = data.major_tags[0];
          headerMajor.innerText = data.political_status ? `${firstMajor} · ${data.political_status}` : firstMajor;
        } else if (data.political_status) {
          headerMajor.innerText = data.political_status;
        } else {
          headerMajor.innerText = '点击前往配置';
        }
      }
    } catch (_) {}
  }

  // DOM 就绪注入
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      injectOmniAgentDrawer();
      bindGlobalHeaderSearch();
      syncGlobalProfileHeader();
    });
  } else {
    injectOmniAgentDrawer();
    bindGlobalHeaderSearch();
    syncGlobalProfileHeader();
  }
})();
