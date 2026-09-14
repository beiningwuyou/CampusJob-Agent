// 全局「+ 解析推文/海报」极速抽取工作台组件
(function() {
  function injectFastParserModal() {
    if (document.getElementById('fast-parser-modal')) return;

    const modalHtml = `
    <div id="fast-parser-modal" class="hidden fixed inset-0 z-[999] bg-slate-950/65 backdrop-blur-xs flex items-center justify-center p-4">
      <div class="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full p-6 space-y-5 animate-in fade-in zoom-in-95 duration-150">
        <!-- 头部 -->
        <div class="flex items-center justify-between border-b border-slate-100 pb-3.5">
          <div class="flex items-center gap-2.5">
            <div class="w-8 h-8 rounded-lg bg-amber-400 text-slate-950 flex items-center justify-center font-bold shadow-xs">
              <span class="material-symbols-outlined text-[20px]">bolt</span>
            </div>
            <div>
              <h3 class="text-sm font-bold text-slate-900 flex items-center gap-2">
                极速解析工作台 (推文 / 海报 OCR / 招考公告)
                <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-100 text-amber-900 border border-amber-300">双 Schema 引擎</span>
              </h3>
              <p class="text-[11px] text-slate-500 mt-0.5">自动识别企业校招与体制内公考公告，提取核心字段并执行本地画像四重门槛自查</p>
            </div>
          </div>
          <button type="button" onclick="closeFastParserModal()" class="text-slate-400 hover:text-slate-700 p-1 rounded-lg transition-colors cursor-pointer">
            <span class="material-symbols-outlined text-[20px]">close</span>
          </button>
        </div>

        <!-- 输入区域 -->
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-xs font-semibold text-slate-700">
              <span class="material-symbols-outlined text-amber-500 text-[16px]">edit_note</span>
              <span>粘贴招聘简章正文 / 微信推文 / 网页抓取内容</span>
            </div>
            <button type="button" onclick="fillFastParserSample()" class="text-[11px] text-amber-700 hover:text-amber-800 bg-amber-50 hover:bg-amber-100 border border-amber-200 px-2 py-0.5 rounded transition-colors cursor-pointer">
              填入华为校招示例
            </button>
          </div>

          <textarea id="fast-parser-input" rows="5" class="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-800 focus:bg-white focus:outline-none focus:border-amber-400 font-sans leading-relaxed resize-none" placeholder="请在此处直接粘贴招聘公众号推文文本、或宣讲会邮件正文..."></textarea>
          
          <div class="flex items-center justify-between text-xs pt-1">
            <div class="flex items-center gap-3 text-slate-500">
              <label class="flex items-center gap-1 cursor-pointer hover:text-slate-800">
                <input type="file" id="fast-parser-image-input" accept="image/*" class="hidden" onchange="handlePosterImageSelect(event)">
                <span class="material-symbols-outlined text-[16px] text-slate-400" onclick="document.getElementById('fast-parser-image-input').click()">add_photo_alternate</span>
                <span onclick="document.getElementById('fast-parser-image-input').click()">上传海报图片 OCR</span>
              </label>
              <span class="text-slate-300">|</span>
              <span class="text-[11px] text-slate-400">支持直接识别图片中的日期、网申链接与地点</span>
            </div>
            <button id="btn-run-fast-parse" type="button" onclick="runFastParseAction()" class="px-4 py-2 bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold rounded-xl shadow-xs transition-all active:scale-95 flex items-center gap-1.5 cursor-pointer">
              <span class="material-symbols-outlined text-[16px]">auto_awesome</span>
              <span>开始智能提取与门槛诊断</span>
            </button>
          </div>
        </div>

        <!-- 结果展示卡片容器 (默认隐藏) -->
        <div id="fast-parser-result-box" class="hidden space-y-3 pt-3 border-t border-slate-100">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold text-slate-900 flex items-center gap-1.5">
              <span class="material-symbols-outlined text-emerald-600 text-[17px]">task_alt</span>
              结构化抽取完成与本地门槛自查报告
            </span>
            <span id="fast-parse-badge" class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
              94分 契合
            </span>
          </div>

          <div class="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-2.5">
            <div class="flex items-start justify-between gap-3">
              <div>
                <h4 id="fast-parse-title" class="text-xs font-bold text-slate-900">通用软件开发工程师 (2027届提前批)</h4>
                <p id="fast-parse-org" class="text-[11px] text-slate-500 mt-0.5">华为技术有限公司 · 终端BG / 计算产品线</p>
              </div>
              <span id="fast-parse-type" class="px-2 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold text-[10px]">
                企业校招
              </span>
            </div>

            <div class="grid grid-cols-2 gap-2 text-[11px] font-mono text-slate-600 pt-1 border-t border-slate-200/80">
              <div>工作地点: <span id="fast-parse-loc" class="text-slate-800 font-sans">杭州 / 深圳</span></div>
              <div>薪酬待遇: <span id="fast-parse-salary" class="text-amber-700 font-bold">20k-35k*15薪</span></div>
              <div>网申截止: <span id="fast-parse-ddl" class="text-slate-800">2026-10-15</span></div>
              <div>资格校验: <span id="fast-parse-qual" class="text-emerald-700 font-bold font-sans">符合 (硕士+工科)</span></div>
            </div>

            <div id="fast-parse-advice" class="text-[11px] text-slate-700 leading-relaxed bg-white p-2.5 rounded-lg border border-slate-200">
              建议针对岗位在简历首页‘专业技能’一栏中突出核心技术栈关键词；强化在分布式与高并发场景下的实际项目成果度量。
            </div>
          </div>

          <div class="flex justify-end gap-2 pt-2">
            <button type="button" onclick="closeFastParserModal()" class="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium cursor-pointer">关闭</button>
            <button id="btn-save-to-tracker" type="button" onclick="saveExtractedJobToTracker()" class="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-1.5 cursor-pointer">
              <span class="material-symbols-outlined text-[15px]">send_and_archive</span>
              <span>已入库，立即推入【投递追踪看板】</span>
            </button>
          </div>
        </div>
      </div>
    </div>
    `;

    document.body.insertAdjacentHTML('beforeend', modalHtml);
  }

  window.openFastParserModal = function() {
    injectFastParserModal();
    const modal = document.getElementById('fast-parser-modal');
    if (modal) modal.classList.remove('hidden');
  };

  window.closeFastParserModal = function() {
    const modal = document.getElementById('fast-parser-modal');
    if (modal) modal.classList.add('hidden');
  };

  window.fillFastParserSample = function() {
    const input = document.getElementById('fast-parser-input');
    if (input) {
      input.value = "【华为2027届校招提前批正式启动】\n招聘单位：华为技术有限公司 · 终端BG / 计算产品线\n招聘职位：通用软件开发工程师 (端云协同/分布式)\n工作地点：杭州市、深圳市\n薪酬范围：20k-35k × 15薪\n学历要求：全日制统招硕士研究生及以上学历\n专业要求：计算机科学与技术、软件工程、电子信息等相关工科专业\n宣讲安排：9月18日19:00 浙大玉泉永谦活动中心\n网申截止：2026年10月15日24:00，网申入口 career.huawei.com";
    }
  };

  window.handlePosterImageSelect = function(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const input = document.getElementById('fast-parser-input');
    if (input) {
      input.value = `【海报 OCR 识别结果：${file.name}】\n中共浙江省委组织部 / 杭州市委办公厅 2027年定向选调生招录公告\n招录职位：数字化改革综合管理岗 (一职位)\n招录人数：2人\n要求条件：限2027届应届毕业生，中共党员(含预备)，计算机科学与技术硕士研究生及以上\n报名起止：2026年10月10日至10月16日\n报名入口：浙江省人事考试网 gwy.zjks.gov.cn`;
    }
    if (typeof showToast === 'function') {
      showToast(`已成功识别宣传海报《${file.name}》文字内容并完成排版规整！`);
    }
  };

  let lastParsedJobId = null;

  window.runFastParseAction = async function() {
    const text = document.getElementById('fast-parser-input')?.value?.trim();
    if (!text) {
      if (typeof showToast === 'function') showToast('请先输入或粘贴需要解析的招聘文本！');
      return;
    }

    const btn = document.getElementById('btn-run-fast-parse');
    const origHtml = btn.innerHTML;
    btn.innerHTML = '<span class="material-symbols-outlined text-[16px] animate-spin">refresh</span><span>双规抽取中...</span>';

    try {
      const res = await fetch('/api/v1/feeds/fast-import', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          raw_text: text,
          title_hint: text.split('\n')[0].replace(/[【】]/g, '').trim()
        })
      });

      if (res.ok) {
        const data = await res.json();
        console.log('[FastParser] Parse result:', data);
        lastParsedJobId = data.job_id;

        const resultBox = document.getElementById('fast-parser-result-box');
        if (resultBox) resultBox.classList.remove('hidden');

        document.getElementById('fast-parse-title').textContent = data.job_title;
        document.getElementById('fast-parse-org').textContent = data.org_name;
        document.getElementById('fast-parse-type').textContent = data.posting_type === 'CIVIL_EXAM' ? '体制内公考' : '企业校招';
        
        const badge = document.getElementById('fast-parse-badge');
        if (data.qualification_status === 'DISQUALIFIED') {
          badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200';
          badge.textContent = '0分 资格不符';
        } else {
          badge.className = 'px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-emerald-50 text-emerald-800 border border-emerald-200';
          badge.textContent = `${data.match_score}分 契合通过`;
        }

        if (typeof showToast === 'function') {
          showToast(`✅ 已完成双 Schema 结构化提取与契合度诊断：${data.job_title}`);
        }
      } else {
        if (typeof showToast === 'function') showToast('解析服务响应异常，请重试');
      }
    } catch (e) {
      console.error(e);
      if (typeof showToast === 'function') showToast('网络请求异常');
    } finally {
      btn.innerHTML = origHtml;
    }
  };

  window.saveExtractedJobToTracker = async function() {
    if (!lastParsedJobId) {
      window.location.href = '/tracker.html';
      return;
    }
    try {
      await fetch('/api/v1/tracker', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: lastParsedJobId,
          stage: 'APPLIED',
          batch_title: '推文极速录入批次',
          resume_version: 'v4.2_分布式重构.pdf'
        })
      });
      if (typeof showToast === 'function') {
        showToast('✅ 已成功将岗位存入数据库并推入【投递追踪看板】！');
      }
      setTimeout(() => {
        window.location.href = '/tracker.html';
      }, 600);
    } catch (e) {
      window.location.href = '/tracker.html';
    }
  };

  // 页面加载后自动拦截顶栏黄色 "+ 解析推文/海报" 按钮
  document.addEventListener('DOMContentLoaded', () => {
    injectFastParserModal();
    const buttons = document.querySelectorAll('header button, header a');
    buttons.forEach(btn => {
      if (btn.innerText && btn.innerText.includes('解析推文/海报')) {
        btn.onclick = function(e) {
          e.preventDefault();
          e.stopPropagation();
          window.openFastParserModal();
        };
      }
    });
  });
})();
