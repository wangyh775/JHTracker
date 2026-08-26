/**
 * Hermes Web Component <career-tracker-widget>
 * Enclosed in closed Shadow DOM to eliminate any style contamination with the host page.
 */

class CareerTrackerWidget extends HTMLElement {
  constructor() {
    super();
    this.root = this.attachShadow({ mode: 'open' });
    this.payload = null;
    this.currentTrack = 'Track 1 (控制算法)';
    this.isExpanded = false;
    this.detectedFields = [];
    this.typingEngine = new TypingEngine();
  }

  connectedCallback() {
    this.render();
    this.initDrag();
    this.bindEvents();
  }

  setPayload(payload) {
    this.payload = payload;
    if (payload.matched_track) {
      this.currentTrack = payload.matched_track;
    }
    this.updateUI();
  }

  updateDetectedFields(fields) {
    this.detectedFields = fields;
    this.updateStats();
  }

  render() {
    const savedPos = JSON.parse(localStorage.getItem('hermes_orb_position') || '{"x":null,"y":null}');
    const initX = savedPos.x !== null ? `${savedPos.x}px` : 'auto';
    const initY = savedPos.y !== null ? `${savedPos.y}px` : 'auto';
    const right = savedPos.x === null ? '24px' : 'auto';
    const bottom = savedPos.y === null ? '24px' : 'auto';

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          all: initial;
          font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
          z-index: 2147483647;
          position: fixed;
          left: ${initX};
          top: ${initY};
          right: ${right};
          bottom: ${bottom};
          user-select: none;
        }

        .orb {
          width: 52px;
          height: 52px;
          border-radius: 26px;
          background: linear-gradient(135deg, #10b981 0%, #059669 100%);
          box-shadow: 0 4px 16px rgba(16, 185, 129, 0.4), 0 2px 6px rgba(0,0,0,0.15);
          display: flex;
          align-items: center;
          justify-content: center;
          color: #ffffff;
          font-size: 22px;
          cursor: grab;
          transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .orb:hover {
          transform: scale(1.08);
          box-shadow: 0 6px 20px rgba(16, 185, 129, 0.6);
        }

        .orb:active {
          cursor: grabbing;
        }

        .badge {
          position: absolute;
          top: -2px;
          right: -2px;
          background: #ef4444;
          color: white;
          font-size: 11px;
          font-weight: bold;
          padding: 2px 6px;
          border-radius: 10px;
          border: 2px solid white;
        }

        .card {
          display: none;
          position: absolute;
          bottom: 60px;
          right: 0;
          width: 380px;
          background: #ffffff;
          border-radius: 12px;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2), 0 2px 8px rgba(0,0,0,0.08);
          border: 1px solid #e5e7eb;
          overflow: hidden;
          flex-direction: column;
          color: #1f2937;
          animation: slideUp 0.2s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .card.active {
          display: flex;
        }

        @keyframes slideUp {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .card-header {
          background: #f9fafb;
          padding: 12px 16px;
          border-bottom: 1px solid #e5e7eb;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .card-header h3 {
          margin: 0;
          font-size: 14px;
          font-weight: 700;
          color: #111827;
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 18px;
          color: #9ca3af;
          cursor: pointer;
          padding: 2px 6px;
          border-radius: 4px;
        }
        .close-btn:hover { color: #374151; background: #e5e7eb; }

        .card-body {
          padding: 14px 16px;
          max-height: 420px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 12px;
          font-size: 13px;
        }

        .section {
          background: #f8fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 10px 12px;
        }

        .section-title {
          font-size: 12px;
          font-weight: 600;
          color: #475569;
          margin-bottom: 6px;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        select.track-select {
          width: 100%;
          padding: 6px 10px;
          border-radius: 6px;
          border: 1px solid #cbd5e1;
          background: #ffffff;
          font-size: 12px;
          color: #1e293b;
          outline: none;
        }

        .btn {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          width: 100%;
          padding: 8px 12px;
          border-radius: 6px;
          font-size: 13px;
          font-weight: 600;
          cursor: pointer;
          border: none;
          transition: background 0.15s ease;
        }

        .btn-primary { background: #10b981; color: white; }
        .btn-primary:hover { background: #059669; }

        .btn-secondary { background: #3b82f6; color: white; margin-top: 6px; }
        .btn-secondary:hover { background: #2563eb; }

        .btn-outline {
          background: white;
          border: 1px solid #d1d5db;
          color: #374151;
          margin-top: 6px;
        }
        .btn-outline:hover { background: #f3f4f6; }

        .status-pill {
          display: inline-block;
          font-size: 11px;
          font-weight: 600;
          padding: 2px 8px;
          border-radius: 12px;
          background: #d1fae5;
          color: #065f46;
        }

        .status-warn {
          background: #fef3c7;
          color: #92400e;
        }

        .field-list {
          display: flex;
          flex-direction: column;
          gap: 4px;
          max-height: 120px;
          overflow-y: auto;
          font-size: 12px;
        }

        .field-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 3px 0;
          border-bottom: 1px dashed #e2e8f0;
        }
      </style>

      <div class="orb" id="hermesOrb" title="Hermes 网申助手 (点击展开)">
        🤖
        <span class="badge" id="fieldBadge" style="display:none;">0</span>
      </div>

      <div class="card" id="hermesCard">
        <div class="card-header">
          <h3><span>🤖</span> Hermes 智能网申助手</h3>
          <button class="close-btn" id="closeCardBtn">×</button>
        </div>
        <div class="card-body">
          <div class="section">
            <div class="section-title">
              <span>🎯 目标岗位与匹配轨迹</span>
              <span class="status-pill" id="scorePill">匹配度 90+</span>
            </div>
            <div style="font-weight: 600; color: #0f172a; margin-bottom: 6px;" id="companyJobText">加载中...</div>
            <select class="track-select" id="trackSelect">
              <option value="Track 1 (控制算法)">Track 1: 控制算法岗 (推荐)</option>
              <option value="Track 2 (自动化与嵌入式)">Track 2: 自动化与嵌入式</option>
              <option value="Track 3 (机电与电气工程)">Track 3: 机电与电气工程</option>
              <option value="Track 4 (机械与结构仿真)">Track 4: 机械与结构仿真</option>
            </select>
          </div>

          <div class="section">
            <div class="section-title">
              <span>📄 绑定简历挂载</span>
            </div>
            <div style="font-size: 11px; color: #64748b; word-break: break-all; margin-bottom: 6px;" id="resumePathText">
              无挂载简历
            </div>
            <button class="btn btn-secondary" id="attachResumeBtn">
              ⚡ 一键挂载简历 (CDP 注入)
            </button>
          </div>

          <div class="section">
            <div class="section-title">
              <span>📋 表单感知状态</span>
              <span class="status-pill status-warn" id="stepStats">检测中...</span>
            </div>
            <div class="field-list" id="fieldListContainer">
              <div style="color:#94a3b8;">正在扫描页面表单元素...</div>
            </div>
          </div>

          <div>
            <button class="btn btn-primary" id="startFillBtn">
              ⚡ 拟人打字自动预填本页
            </button>
            <button class="btn btn-outline" id="instantFillBtn">
              ⏩ 极速跳过动画瞬间填完
            </button>
          </div>
        </div>
      </div>
    `;
  }

  initDrag() {
    const orb = this.shadowRoot.getElementById('hermesOrb');
    let isDragging = false;
    let startX, startY, origX, origY;

    orb.addEventListener('mousedown', (e) => {
      if (e.target.id === 'closeCardBtn') return;
      isDragging = true;
      startX = e.clientX;
      startY = e.clientY;
      const rect = this.getBoundingClientRect();
      origX = rect.left;
      origY = rect.top;
      e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      const dx = e.clientX - startX;
      const dy = e.clientY - startY;
      let newX = origX + dx;
      let newY = origY + dy;

      // Boundary
      newX = Math.max(10, Math.min(window.innerWidth - 65, newX));
      newY = Math.max(10, Math.min(window.innerHeight - 65, newY));

      this.style.left = `${newX}px`;
      this.style.top = `${newY}px`;
      this.style.right = 'auto';
      this.style.bottom = 'auto';
    });

    window.addEventListener('mouseup', (e) => {
      if (!isDragging) return;
      isDragging = false;
      const rect = this.getBoundingClientRect();
      localStorage.setItem('hermes_orb_position', JSON.stringify({ x: rect.left, y: rect.top }));
    });
  }

  bindEvents() {
    const orb = this.shadowRoot.getElementById('hermesOrb');
    const card = this.shadowRoot.getElementById('hermesCard');
    const closeBtn = this.shadowRoot.getElementById('closeCardBtn');
    const trackSelect = this.shadowRoot.getElementById('trackSelect');
    const attachResumeBtn = this.shadowRoot.getElementById('attachResumeBtn');
    const startFillBtn = this.shadowRoot.getElementById('startFillBtn');
    const instantFillBtn = this.shadowRoot.getElementById('instantFillBtn');

    orb.addEventListener('click', () => {
      this.isExpanded = !this.isExpanded;
      card.classList.toggle('active', this.isExpanded);
    });

    closeBtn.addEventListener('click', () => {
      this.isExpanded = false;
      card.classList.remove('active');
    });

    trackSelect.addEventListener('change', (e) => {
      this.currentTrack = e.target.value;
      this.onTrackChange(this.currentTrack);
    });

    attachResumeBtn.addEventListener('click', () => {
      this.onAttachResume();
    });

    startFillBtn.addEventListener('click', () => {
      this.onAutofill(false);
    });

    instantFillBtn.addEventListener('click', () => {
      this.onAutofill(true);
    });
  }

  updateUI() {
    if (!this.payload) return;
    const companyJob = this.shadowRoot.getElementById('companyJobText');
    const resumePath = this.shadowRoot.getElementById('resumePathText');
    const scorePill = this.shadowRoot.getElementById('scorePill');
    const trackSelect = this.shadowRoot.getElementById('trackSelect');

    companyJob.innerText = `${this.payload.company_name || '目标公司'} - ${this.payload.position || '岗位'}`;
    scorePill.innerText = `匹配度 ${this.payload.match_score || 90}分`;

    const resume = this.payload.recommended_resume;
    if (resume) {
      resumePath.innerText = `📄 ${resume.file_path || resume.file_name}`;
    }

    if (this.payload.matched_track) {
      trackSelect.value = this.payload.matched_track;
    }
  }

  updateStats() {
    const badge = this.shadowRoot.getElementById('fieldBadge');
    const stepStats = this.shadowRoot.getElementById('stepStats');
    const container = this.shadowRoot.getElementById('fieldListContainer');

    const total = this.detectedFields.length;
    badge.innerText = total;
    badge.style.display = total > 0 ? 'block' : 'none';
    stepStats.innerText = `已识别 ${total} 项`;

    if (total === 0) {
      container.innerHTML = `<div style="color:#94a3b8;">未检测到本页输入项</div>`;
      return;
    }

    container.innerHTML = this.detectedFields.slice(0, 8).map(f => `
      <div class="field-item">
        <span style="font-weight:500;">${f.label}</span>
        <span style="color:#64748b; font-size:11px;">[${f.type}]</span>
      </div>
    `).join('');
  }

  onTrackChange(trackName) {
    if (this.payload && this.payload.track_resumes) {
      const matched = this.payload.track_resumes.find(r => r.track === trackName);
      const resumePath = this.shadowRoot.getElementById('resumePathText');
      if (matched) {
        resumePath.innerText = `📄 ${matched.file_path || matched.file_name}`;
      }
    }
  }

  async onAttachResume() {
    const attachBtn = this.shadowRoot.getElementById('attachResumeBtn');
    attachBtn.innerText = '⏳ 正在通过 CDP 挂载...';
    attachBtn.disabled = true;

    chrome.runtime.sendMessage({
      type: 'ATTACH_RESUME_FILE',
      payload: {
        track: this.currentTrack
      }
    }, (response) => {
      attachBtn.disabled = false;
      if (response && response.success) {
        attachBtn.innerText = '✅ 简历挂载成功';
        attachBtn.style.background = '#059669';
      } else {
        attachBtn.innerText = '⚠️ 挂载失败 (未发现上传框)';
        attachBtn.style.background = '#dc2626';
      }
    });
  }

  async onAutofill(isInstant = false) {
    if (!this.payload) return;
    const startBtn = this.shadowRoot.getElementById('startFillBtn');
    startBtn.disabled = true;
    startBtn.innerText = '⏳ 正在填入表单...';

    const inputs = FormDetector.scan();
    const basics = this.payload.basic_profile || {};
    const openQuestions = this.payload.open_questions || [];

    for (const field of inputs) {
      const label = field.label;
      let matchedVal = null;

      // Match basics
      if (label.includes('姓名') || label.includes('Name')) matchedVal = basics.name;
      else if (label.includes('手机') || label.includes('电话') || label.includes('Phone')) matchedVal = basics.phone;
      else if (label.includes('邮箱') || label.includes('Email') || label.includes('E-mail')) matchedVal = basics.email;
      else if (label.includes('最高学历') || label.includes('学历') || label.includes('Degree')) matchedVal = basics.education;
      else if (label.includes('学校') || label.includes('毕业院校') || label.includes('University')) matchedVal = basics.university;
      else if (label.includes('专业') || label.includes('Major')) matchedVal = basics.major;
      else if (label.includes('求职意向') || label.includes('期望岗位')) matchedVal = this.payload.position;

      // Match open questions
      if (!matchedVal && field.type === 'textarea') {
        const found = openQuestions.find(q => label.includes(q.question) || q.question.includes(label));
        if (found) matchedVal = found.answer;
      }

      if (matchedVal) {
        if (isInstant) {
          this.typingEngine.instantSet(field.element, matchedVal);
        } else {
          await this.typingEngine.typeText(field.element, matchedVal);
        }
      }
    }

    startBtn.disabled = false;
    startBtn.innerText = '⚡ 拟人打字自动预填本页';
    this.updateStats();
  }
}

customElements.define('career-tracker-widget', CareerTrackerWidget);
