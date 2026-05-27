/* TechLib 편집기 클라이언트 로직 */
'use strict';

// ============================================================
// markdown-it 설정 + mermaid 초기화
// ============================================================

const md = window.markdownit({
    html: true,
    linkify: true,
    typographer: true,
    breaks: false,
    highlight: (str, lang) => {
        if (lang && window.hljs && hljs.getLanguage(lang)) {
            try {
                return '<pre class="hljs"><code class="language-' + lang + '">' +
                    hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                    '</code></pre>';
            } catch (_) { /* fallthrough */ }
        }
        return '<pre><code>' + md.utils.escapeHtml(str) + '</code></pre>';
    },
});

if (window.markdownitAnchor) md.use(window.markdownitAnchor.default);
if (window.markdownitTaskLists) md.use(window.markdownitTaskLists);

mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });

// ============================================================
// 상태
// ============================================================

let currentPath = null;
let lastSavedContent = '';
let isDirty = false;

// ============================================================
// DOM
// ============================================================

const $ = (id) => document.getElementById(id);
const editor = $('editor');
const preview = $('preview');
const tree = $('tree');
const statusEl = $('status');
const btnSave = $('btn-save');
const btnNew = $('btn-new');
const editorStats = $('editor-stats');
const syncScroll = $('sync-scroll');

const modal = $('new-modal');
const newSection = $('new-section');
const newTitle = $('new-title');
const newSlug = $('new-slug');
const newSummary = $('new-summary');
const newError = $('new-error');

// ============================================================
// 트리 로드
// ============================================================

async function loadTree() {
    try {
        const r = await fetch('/api/tree');
        const data = await r.json();
        tree.innerHTML = '';
        for (const sec of data.sections) {
            const h = document.createElement('div');
            h.className = 'section-header';
            h.textContent = sec.section;
            tree.appendChild(h);
            for (const f of sec.files) {
                const a = document.createElement('a');
                a.className = 'file-link';
                a.textContent = f.name;
                a.dataset.path = f.path;
                a.title = f.path;
                a.addEventListener('click', () => loadFile(f.path));
                tree.appendChild(a);
            }
        }
    } catch (e) {
        tree.innerHTML = '<div style="color:red;padding:12px">트리 로드 실패: ' + e.message + '</div>';
    }
}

// ============================================================
// 파일 로드 / 저장
// ============================================================

async function loadFile(path) {
    if (isDirty && !confirm('수정 내용이 저장되지 않았습니다. 버리고 다른 파일을 열까요?')) return;
    try {
        const r = await fetch('/api/file?path=' + encodeURIComponent(path));
        const data = await r.json();
        if (!r.ok || data.error) {
            setStatus('error', '로드 실패: ' + (data.error || r.status));
            return;
        }
        currentPath = path;
        editor.value = data.content;
        lastSavedContent = data.content;
        isDirty = false;
        btnSave.disabled = true;
        setStatus('saved', path);
        renderPreview();
        updateStats();
        document.querySelectorAll('.file-link').forEach(el =>
            el.classList.toggle('active', el.dataset.path === path));
    } catch (e) {
        setStatus('error', '로드 오류: ' + e.message);
    }
}

async function saveFile() {
    if (!currentPath) return;
    try {
        const r = await fetch('/api/file', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ path: currentPath, content: editor.value }),
        });
        const data = await r.json();
        if (!r.ok || data.error) {
            setStatus('error', '저장 실패: ' + (data.error || r.status));
            return;
        }
        lastSavedContent = editor.value;
        isDirty = false;
        btnSave.disabled = true;
        setStatus('saved', `저장됨 · ${data.bytes} bytes · ${currentPath}`);
    } catch (e) {
        setStatus('error', '저장 오류: ' + e.message);
    }
}

function setStatus(kind, text) {
    statusEl.className = 'status ' + (kind || '');
    statusEl.textContent = text;
}

function updateStats() {
    const lines = editor.value.split('\n').length;
    const chars = editor.value.length;
    editorStats.textContent = `${lines}줄 · ${chars}자`;
}

// ============================================================
// 미리보기 렌더
// ============================================================

let previewTimer = null;

function renderPreview() {
    const text = editor.value;
    if (!text.trim()) {
        preview.innerHTML = '<em class="hint">편집을 시작하면 여기에 미리보기가 표시됩니다.</em>';
        return;
    }
    // mermaid 블록을 일반 코드블록 대신 div.mermaid로 치환
    const mermaidBlocks = [];
    let prepared = text.replace(/```mermaid\n([\s\S]*?)```/g, (m, code) => {
        mermaidBlocks.push(code);
        return `\n\n[[MERMAID_${mermaidBlocks.length - 1}]]\n\n`;
    });

    let html = md.render(prepared);
    html = html.replace(/<p>\[\[MERMAID_(\d+)\]\]<\/p>/g, (m, idx) => {
        const code = mermaidBlocks[parseInt(idx, 10)];
        return `<div class="mermaid">${escapeHtml(code)}</div>`;
    });
    preview.innerHTML = html;

    // mermaid 렌더
    try {
        mermaid.run({ querySelector: '#preview .mermaid' });
    } catch (e) {
        console.warn('mermaid render error', e);
    }
}

function escapeHtml(s) {
    return s.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
}

// ============================================================
// 편집기 이벤트
// ============================================================

editor.addEventListener('input', () => {
    isDirty = (editor.value !== lastSavedContent);
    btnSave.disabled = !isDirty;
    setStatus(isDirty ? 'dirty' : 'saved', isDirty ? `수정됨 · ${currentPath || ''}` : (currentPath || ''));
    updateStats();
    clearTimeout(previewTimer);
    previewTimer = setTimeout(renderPreview, 180);
});

editor.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
        e.preventDefault();
        saveFile();
    }
});

window.addEventListener('beforeunload', (e) => {
    if (isDirty) { e.preventDefault(); e.returnValue = ''; }
});

btnSave.addEventListener('click', saveFile);

// ============================================================
// 스크롤 동기화
// ============================================================

editor.addEventListener('scroll', () => {
    if (!syncScroll.checked) return;
    const ratio = editor.scrollTop / Math.max(1, editor.scrollHeight - editor.clientHeight);
    preview.scrollTop = ratio * Math.max(1, preview.scrollHeight - preview.clientHeight);
});

// ============================================================
// 편집 보조 도구 (첨삭 헬퍼)
// ============================================================

const SNIPPETS = {
    todo: () => `<!-- TODO: ${prompt('TODO 내용:', '') || ''} -->`,
    note: () => `\n<!--\n메모: ${prompt('비공개 메모:', '') || ''}\n-->\n`,
    code: () => '\n```cpp\n// Unreal 친화 예시\n\n```\n',
    table: () => '\n| 항목 | 설명 |\n| --- | --- |\n| A | ... |\n| B | ... |\n',
    mermaid: () => '\n```mermaid\nflowchart LR\n    A[시작] --> B{판단}\n    B -->|예| C[처리 A]\n    B -->|아니오| D[처리 B]\n```\n',
    link: () => {
        const label = prompt('표시 텍스트:', '') || '관련 페이지';
        const path = prompt('상대 경로 (예: ../01-data-structures/tree-graph.md):', '') || '../path.md';
        return `[${label}](${path})`;
    },
};

document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        const fn = SNIPPETS[action];
        if (!fn) return;
        insertAtCursor(fn());
    });
});

function insertAtCursor(text) {
    const start = editor.selectionStart;
    const end = editor.selectionEnd;
    const before = editor.value.substring(0, start);
    const selected = editor.value.substring(start, end);
    const after = editor.value.substring(end);
    editor.value = before + text + after;
    editor.selectionStart = editor.selectionEnd = start + text.length;
    editor.focus();
    // input 이벤트 강제 발생
    editor.dispatchEvent(new Event('input'));
}

// ============================================================
// 새 페이지 모달
// ============================================================

btnNew.addEventListener('click', async () => {
    newError.hidden = true;
    newTitle.value = '';
    newSlug.value = '';
    newSummary.value = '';
    try {
        const r = await fetch('/api/sections');
        const data = await r.json();
        newSection.innerHTML = '';
        for (const s of data.sections) {
            const o = document.createElement('option');
            o.value = s.name;
            o.textContent = s.name + (s.multipage ? '' : '  (단일→다중 변환됨)');
            newSection.appendChild(o);
        }
        modal.hidden = false;
        newTitle.focus();
    } catch (e) {
        alert('섹션 목록 로드 실패: ' + e.message);
    }
});

$('btn-cancel').addEventListener('click', () => { modal.hidden = true; });

$('btn-create').addEventListener('click', async () => {
    newError.hidden = true;
    const section = newSection.value;
    const title = newTitle.value.trim();
    const slug = newSlug.value.trim();
    const summary = newSummary.value.trim();
    if (!title || !slug) {
        newError.textContent = '제목과 슬러그는 필수입니다.';
        newError.hidden = false;
        return;
    }
    if (!/^[a-z0-9][a-z0-9-]*$/.test(slug)) {
        newError.textContent = '슬러그는 영문 소문자·숫자·하이픈만 사용 (예: hash-table)';
        newError.hidden = false;
        return;
    }
    try {
        const r = await fetch('/api/page', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section, title, slug, summary }),
        });
        const data = await r.json();
        if (!r.ok || data.error) {
            newError.textContent = '생성 실패: ' + (data.error || r.status);
            newError.hidden = false;
            return;
        }
        modal.hidden = true;
        await loadTree();
        await loadFile(data.path);
    } catch (e) {
        newError.textContent = '오류: ' + e.message;
        newError.hidden = false;
    }
});

// 모달 외부 클릭으로 닫기
modal.addEventListener('click', (e) => {
    if (e.target === modal) modal.hidden = true;
});

// Esc 키
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && !modal.hidden) modal.hidden = true;
});

// ============================================================
// 초기 로드
// ============================================================

loadTree();
updateStats();
