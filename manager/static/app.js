(() => {
    "use strict";

    const POLL_INTERVAL_MS = 3000;

    const els = {
        installScreen:   document.getElementById("install-screen"),
        dashboard:       document.getElementById("dashboard"),
        btnInstall:      document.getElementById("btn-install"),
        installProgress: document.getElementById("install-progress"),
        installMessage:  document.getElementById("install-message"),
        installPercent:  document.getElementById("install-percent"),
        installBar:      document.getElementById("install-bar"),
        installError:    document.getElementById("install-error"),
        containersGrid:  document.getElementById("containers-grid"),
        logsPanel:       document.getElementById("logs-panel"),
        logsContent:     document.getElementById("logs-content"),
        logsName:        document.getElementById("logs-container-name"),
        logsClose:       document.getElementById("logs-close"),
        dockerInfo:      document.getElementById("docker-info"),
    };

    let selectedLogContainer = null;
    let pollTimer = null;

    // ---- Утилиты ---------------------------------------------------------

    const fmtUptime = (s) => {
        if (s == null) return "—";
        const d = Math.floor(s / 86400);
        const h = Math.floor((s % 86400) / 3600);
        const m = Math.floor((s % 3600) / 60);
        const sec = s % 60;
        if (d) return `${d}д ${h}ч`;
        if (h) return `${h}ч ${m}м`;
        if (m) return `${m}м ${sec}с`;
        return `${sec}с`;
    };

    const statusStyle = (status) => {
        switch (status) {
            case "running": return { dot: "bg-green-400", label: "Работает", cls: "text-green-300" };
            case "exited":  return { dot: "bg-red-500",   label: "Остановлен", cls: "text-red-300" };
            case "paused":  return { dot: "bg-yellow-400", label: "Пауза", cls: "text-yellow-300" };
            case "restarting": return { dot: "bg-yellow-400", label: "Перезапуск", cls: "text-yellow-300" };
            case "missing": return { dot: "bg-slate-600", label: "Отсутствует", cls: "text-slate-400" };
            default:        return { dot: "bg-slate-500", label: status, cls: "text-slate-300" };
        }
    };

    const esc = (str) => String(str).replace(/[&<>"']/g, (c) => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    }[c]));

    // ---- Рендер карточки контейнера -------------------------------------

    const renderCard = (c) => {
        const s = statusStyle(c.status);
        const running = c.status === "running";
        const exists = c.status !== "missing";
        return `
            <div class="bg-slate-800/50 border border-slate-700 rounded-xl p-5 hover:border-slate-600 transition" data-container="${esc(c.name)}">
                <div class="flex items-start justify-between mb-3">
                    <div class="min-w-0">
                        <div class="text-sm font-mono font-semibold truncate">${esc(c.name)}</div>
                        <div class="text-xs text-slate-500 truncate mt-0.5">${esc(c.image || "—")}</div>
                    </div>
                    <span class="flex items-center gap-2 text-xs ${s.cls} shrink-0">
                        <span class="w-2 h-2 rounded-full ${s.dot}"></span> ${s.label}
                    </span>
                </div>

                <div class="grid grid-cols-2 gap-2 mb-3 text-xs">
                    <div class="bg-slate-900/60 rounded p-2">
                        <div class="text-slate-500">CPU</div>
                        <div class="font-mono ${running ? "text-indigo-300" : "text-slate-600"}">${c.cpu_percent.toFixed(1)}%</div>
                    </div>
                    <div class="bg-slate-900/60 rounded p-2">
                        <div class="text-slate-500">RAM</div>
                        <div class="font-mono ${running ? "text-indigo-300" : "text-slate-600"}">${c.mem_usage_mb.toFixed(0)} / ${c.mem_limit_mb.toFixed(0)} МБ</div>
                    </div>
                    <div class="bg-slate-900/60 rounded p-2 col-span-2">
                        <div class="text-slate-500">Uptime</div>
                        <div class="font-mono ${running ? "text-indigo-300" : "text-slate-600"}">${fmtUptime(c.uptime_seconds)}</div>
                    </div>
                </div>

                <div class="flex gap-2 flex-wrap">
                    ${running
                        ? `<button data-action="stop" data-name="${esc(c.name)}" class="px-3 py-1.5 text-xs bg-red-950 hover:bg-red-900 border border-red-800 text-red-300 rounded-lg transition">⏹ Стоп</button>`
                        : `<button data-action="start" data-name="${esc(c.name)}" ${!exists ? "disabled" : ""} class="px-3 py-1.5 text-xs bg-green-950 hover:bg-green-900 border border-green-800 text-green-300 rounded-lg transition disabled:opacity-40 disabled:cursor-not-allowed">▶ Старт</button>`
                    }
                    <button data-action="restart" data-name="${esc(c.name)}" ${!exists ? "disabled" : ""} class="px-3 py-1.5 text-xs bg-slate-900 hover:bg-slate-700 border border-slate-700 text-slate-300 rounded-lg transition disabled:opacity-40 disabled:cursor-not-allowed">⟳ Рестарт</button>
                    <button data-action="logs" data-name="${esc(c.name)}" ${!exists ? "disabled" : ""} class="px-3 py-1.5 text-xs bg-indigo-950 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 rounded-lg transition disabled:opacity-40 disabled:cursor-not-allowed">📄 Логи</button>
                </div>
            </div>
        `;
    };

    // ---- Рендер состояний ------------------------------------------------

    const showInstallIdle = () => {
        els.installScreen.classList.remove("hidden");
        els.dashboard.classList.add("hidden");
        els.btnInstall.disabled = false;
        els.btnInstall.textContent = "🚀 Запустить установку (Bootstrap)";
        els.installProgress.classList.add("hidden");
        els.installError.classList.add("hidden");
    };

    const showInstallProgress = (data) => {
        els.installScreen.classList.remove("hidden");
        els.dashboard.classList.add("hidden");
        els.btnInstall.disabled = true;
        els.btnInstall.textContent = "Установка…";
        els.installProgress.classList.remove("hidden");
        els.installMessage.textContent = data.message || "Установка…";
        els.installPercent.textContent = (data.progress || 0) + "%";
        els.installBar.style.width = (data.progress || 0) + "%";
        if (data.error) {
            els.installError.classList.remove("hidden");
            els.installError.textContent = data.error;
        } else {
            els.installError.classList.add("hidden");
        }
    };

    const showDashboard = (data) => {
        els.installScreen.classList.add("hidden");
        els.dashboard.classList.remove("hidden");

        els.containersGrid.innerHTML = data.containers.map(renderCard).join("");

        if (data.docker) {
            els.dockerInfo.innerHTML =
                `Docker ${esc(data.docker.server_version || "?")} · ` +
                `${data.docker.containers_running}/${data.docker.containers_total} запущено` +
                (data.docker.gpu_available ? ` · <span class="text-green-400">GPU</span>` : "");
        }

        if (selectedLogContainer) {
            refreshLogs();
        }
    };

    // ---- Загрузка логов --------------------------------------------------

    const refreshLogs = async () => {
        if (!selectedLogContainer) return;
        try {
            const r = await fetch(`/api/containers/${encodeURIComponent(selectedLogContainer)}/logs?tail=200`);
            if (!r.ok) throw new Error("logs fetch failed");
            const data = await r.json();
            els.logsName.textContent = selectedLogContainer;
            els.logsPanel.classList.remove("hidden");
            const nearBottom =
                els.logsContent.scrollTop + els.logsContent.clientHeight >= els.logsContent.scrollHeight - 40;
            els.logsContent.textContent = data.logs || "(пусто)";
            if (nearBottom) els.logsContent.scrollTop = els.logsContent.scrollHeight;
        } catch (e) {
            els.logsContent.textContent = "Ошибка загрузки логов: " + e.message;
        }
    };

    const openLogs = (name) => {
        selectedLogContainer = name;
        els.logsPanel.classList.remove("hidden");
        refreshLogs();
        els.logsPanel.scrollIntoView({ behavior: "smooth", block: "start" });
    };

    const closeLogs = () => {
        selectedLogContainer = null;
        els.logsPanel.classList.add("hidden");
    };

    // ---- API -------------------------------------------------------------

    const apiPost = async (url) => {
        const r = await fetch(url, { method: "POST" });
        const data = await r.json().catch(() => ({}));
        if (!r.ok) throw new Error(data.detail || `HTTP ${r.status}`);
        return data;
    };

    const controlContainer = async (name, action) => {
        try {
            await apiPost(`/api/containers/${encodeURIComponent(name)}/${action}`);
            await poll();
        } catch (e) {
            alert(`Ошибка ${action} для ${name}: ${e.message}`);
        }
    };

    // ---- Поллинг ---------------------------------------------------------

    const poll = async () => {
        try {
            const r = await fetch("/api/installer/status");
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            const data = await r.json();

            if (data.installing) {
                showInstallProgress(data);
            } else if (!data.installed) {
                if (data.error) {
                    showInstallProgress(data);
                } else {
                    showInstallIdle();
                }
            } else {
                showDashboard(data);
            }
        } catch (e) {
            console.error("status poll error", e);
        } finally {
            clearTimeout(pollTimer);
            pollTimer = setTimeout(poll, POLL_INTERVAL_MS);
        }
    };

    // ---- Обработчики -----------------------------------------------------

    els.btnInstall.addEventListener("click", async () => {
        els.btnInstall.disabled = true;
        els.btnInstall.textContent = "Установка…";
        try {
            await apiPost("/api/installer/bootstrap");
            await poll();
        } catch (e) {
            els.installError.classList.remove("hidden");
            els.installError.textContent = e.message;
            els.btnInstall.disabled = false;
            els.btnInstall.textContent = "🚀 Запустить установку (Bootstrap)";
        }
    });

    els.containersGrid.addEventListener("click", (ev) => {
        const btn = ev.target.closest("button[data-action]");
        if (!btn || btn.disabled) return;
        const action = btn.dataset.action;
        const name = btn.dataset.name;
        if (action === "logs") openLogs(name);
        else controlContainer(name, action);
    });

    els.logsClose.addEventListener("click", closeLogs);

    // Старт
    poll();
})();