// ---- Глобальные переменные (задачи) ----
let currentDate = new Date();
currentDate.setHours(0, 0, 0, 0);
let allTasksForCalendar = [];
let displayedWeekStart = null;
let currentWeekStart = null;
let prevWeekStart = null;
let nextWeekStart = null;

// ---- Глобальные переменные (события) ----
let allEventsForCalendar = [];

// ---- Вспомогательные функции ----
function formatYMD(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, '0');
    const d = String(date.getDate()).padStart(2, '0');
    return `${y}-${m}-${d}`;
}

function formatDateRange(startDate) {
    const start = new Date(startDate);
    const end = new Date(startDate);
    end.setDate(end.getDate() + 6);
    const options = { day: 'numeric', month: 'short' };
    return `${start.toLocaleDateString('ru-RU', options)} – ${end.toLocaleDateString('ru-RU', options)}`;
}

// ---- Загрузка информации о текущей неделе ----
async function loadWeekInfo() {
    try {
        const res = await fetch('/api/tasks/week/current');
        const data = await res.json();
        currentWeekStart = new Date(data.week_start);
        prevWeekStart = new Date(currentWeekStart);
        prevWeekStart.setDate(prevWeekStart.getDate() - 7);
        nextWeekStart = new Date(currentWeekStart);
        nextWeekStart.setDate(nextWeekStart.getDate() + 7);
        if (!displayedWeekStart) {
            displayedWeekStart = new Date(currentWeekStart);
        }
        document.getElementById('weekRange').innerText = formatDateRange(displayedWeekStart);
    } catch (error) {
        console.error('Ошибка загрузки недели', error);
    }
}

// ---- Загрузка задач для календаря (цветные точки) ----
async function loadTasksForWeek() {
    if (!displayedWeekStart) return;
    const start = new Date(displayedWeekStart);
    start.setHours(0,0,0,0);
    const end = new Date(displayedWeekStart);
    end.setDate(end.getDate() + 7);
    end.setHours(0,0,0,0);
    const startParam = formatYMD(start);
    const endParam = formatYMD(end);
    try {
        const response = await fetch(`/api/tasks?start_date=${startParam}&end_date=${endParam}`);
        if (!response.ok) throw new Error();
        allTasksForCalendar = await response.json();
        renderCalendar();
    } catch (error) {
        console.error('Ошибка загрузки задач для недели', error);
    }
}

// ---- Загрузка всех событий для календаря (синие точки) ----
async function loadAllEventsForCalendar() {
    try {
        const res = await fetch('/api/events/all');
        if (!res.ok) throw new Error();
        allEventsForCalendar = await res.json();
        renderCalendar();
    } catch (error) {
        console.error('Ошибка загрузки событий', error);
    }
}

// ---- Отрисовка календаря (задачи + события) ----
function renderCalendar() {
    if (!displayedWeekStart) return;
    const container = document.getElementById('weekCalendar');
    container.innerHTML = '';
    const dayNames = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];
    const monday = new Date(displayedWeekStart);
    for (let i = 0; i < 7; i++) {
        const dayDate = new Date(monday);
        dayDate.setDate(monday.getDate() + i);
        const ymd = formatYMD(dayDate);
        const prioritiesSet = new Set();
        allTasksForCalendar.forEach(task => {
            const taskDate = task.start_time.split('T')[0];
            if (taskDate === ymd) prioritiesSet.add(task.priority);
        });
        const hasGreen = prioritiesSet.has('Низкая');
        const hasYellow = prioritiesSet.has('Средняя');
        const hasRed = prioritiesSet.has('Высокая');
        const hasBlack = prioritiesSet.has('Очень высокая');
        const hasEvent = allEventsForCalendar.some(ev => ev.event_date === ymd);
        const hasDeadline = allDeadlines.some(d =>
            !d.is_completed && formatYMD(new Date(d.deadline_time)) === ymd
        );

        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        if (formatYMD(currentDate) === ymd) dayCard.classList.add('active');
        dayCard.innerHTML = `
            ${hasEvent ? '<span class="event-dot"></span>' : ''}
            ${hasDeadline ? '<span class="deadline-dot"></span>' : ''}
            <div class="day-name">${dayNames[i]}</div>
            <div class="day-number">${dayDate.getDate()}</div>
            <div class="priority-dots">
                ${hasGreen ? '<span class="dot dot-green"></span>' : ''}
                ${hasYellow ? '<span class="dot dot-yellow"></span>' : ''}
                ${hasRed ? '<span class="dot dot-red"></span>' : ''}
                ${hasBlack ? '<span class="dot dot-black"></span>' : ''}
            </div>
        `;
        dayCard.addEventListener('click', () => {
            currentDate = new Date(dayDate);
            currentDate.setHours(0,0,0,0);
            loadTasksForCurrentDate();
            loadEventsForDate(currentDate);
            renderCalendar();
        });
        container.appendChild(dayCard);
    }
}

// ---- Загрузка задач для выбранного дня ----
async function loadTasksForCurrentDate() {
    const container = document.getElementById('tasks-container');
    container.innerHTML = '<div class="loading">Загрузка...</div>';
    const dateParam = formatYMD(currentDate);
    try {
        const response = await fetch(`/api/tasks?start_date=${dateParam}&end_date=${dateParam}`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const tasks = await response.json();
        if (!tasks.length) {
            container.innerHTML = '<div class="error">Нет задач на этот день</div>';
            updateStats([]);
            return;
        }
        displayTasks(tasks);
        updateStats(tasks);
    } catch (error) {
        container.innerHTML = `<div class="error">Ошибка: ${error.message}</div>`;
    }
}

// ---- Навигация по неделям ----
function prevWeek() {
    if (!displayedWeekStart) return;
    const currentYMD = formatYMD(displayedWeekStart);
    const prevYMD = formatYMD(prevWeekStart);
    const currYMD = formatYMD(currentWeekStart);
    if (currentYMD === prevYMD) return;
    if (currentYMD === currYMD) {
        displayedWeekStart = new Date(prevWeekStart);
    } else if (currentYMD === formatYMD(nextWeekStart)) {
        displayedWeekStart = new Date(currentWeekStart);
    }
    updateWeekDisplayAndLoad();
}

function nextWeek() {
    if (!displayedWeekStart) return;
    const currentYMD = formatYMD(displayedWeekStart);
    const nextYMD = formatYMD(nextWeekStart);
    const currYMD = formatYMD(currentWeekStart);
    if (currentYMD === nextYMD) return;
    if (currentYMD === currYMD) {
        displayedWeekStart = new Date(nextWeekStart);
    } else if (currentYMD === formatYMD(prevWeekStart)) {
        displayedWeekStart = new Date(currentWeekStart);
    }
    updateWeekDisplayAndLoad();
}

function updateWeekDisplayAndLoad() {
    document.getElementById('weekRange').innerText = formatDateRange(displayedWeekStart);
    loadTasksForWeek().then(() => {
        const weekStart = new Date(displayedWeekStart);
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 7);
        if (currentDate < weekStart || currentDate >= weekEnd) {
            currentDate = new Date(weekStart);
            loadTasksForCurrentDate();
            loadEventsForDate(currentDate);
        }
        renderCalendar();
    });
}

// ---- Функции для событий ----
async function loadEventsForDate(date) {
    const ymd = formatYMD(date);
    try {
        const res = await fetch(`/api/events/${ymd}`);
        if (!res.ok) throw new Error();
        const events = await res.json();
        const container = document.getElementById('eventsList');
        if (!events.length) {
            container.innerHTML = '<div class="no-events">В этот день нет событий</div>';
            return;
        }
        container.innerHTML = events.map(ev => `
            <div class="event-item" data-id="${ev.id}">
                <span class="event-name">${escapeHtml(ev.name)}</span>
                <div class="event-actions">
                    <button class="edit-event" data-id="${ev.id}">✏️</button>
                    <button class="delete-event" data-id="${ev.id}">🗑️</button>
                </div>
            </div>
        `).join('');
        document.querySelectorAll('.edit-event').forEach(btn => {
            btn.onclick = () => openEventModal(parseInt(btn.dataset.id));
        });
        document.querySelectorAll('.delete-event').forEach(btn => {
            btn.onclick = () => deleteEvent(parseInt(btn.dataset.id));
        });
    } catch (error) {
        console.error('Ошибка загрузки событий', error);
    }
}

function openEventModal(eventId = null) {
    const modal = document.getElementById('eventModal');
    const form = document.getElementById('eventForm');
    form.reset();
    document.getElementById('editEventId').value = '';
    document.getElementById('eventModalTitle').innerText = 'Новое событие';
    if (eventId) {
        document.getElementById('eventModalTitle').innerText = 'Редактировать событие';
        fetch(`/api/events/${formatYMD(currentDate)}`)
            .then(res => res.json())
            .then(events => {
                const ev = events.find(e => e.id === eventId);
                if (ev) {
                    document.getElementById('eventName').value = ev.name;
                    document.getElementById('eventDate').value = ev.event_date;
                    document.getElementById('editEventId').value = ev.id;
                }
            });
    } else {
        document.getElementById('eventDate').value = formatYMD(currentDate);
    }
    modal.style.display = 'flex';
}

async function saveEvent(event) {
    event.preventDefault();
    const name = document.getElementById('eventName').value.trim();
    const eventDate = document.getElementById('eventDate').value;
    const editId = document.getElementById('editEventId').value;
    if (!name || !eventDate) {
        alert('Заполните название и дату');
        return;
    }
    const payload = { name, event_date: eventDate };
    try {
        let url = '/api/events', method = 'POST';
        if (editId) {
            url = `/api/events/${editId}`;
            method = 'PUT';
        }
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeEventModal();
            await loadAllEventsForCalendar();
            await loadEventsForDate(currentDate);
        } else {
            const err = await res.json();
            alert('Ошибка: ' + (err.detail || 'Не удалось сохранить событие'));
        }
    } catch (error) {
        alert('Ошибка соединения: ' + error.message);
    }
}

async function deleteEvent(eventId) {
    if (confirm('Удалить событие?')) {
        try {
            const res = await fetch(`/api/events/${eventId}`, { method: 'DELETE' });
            if (res.ok) {
                await loadAllEventsForCalendar();
                await loadEventsForDate(currentDate);
            } else {
                alert('Ошибка удаления');
            }
        } catch (error) {
            alert('Ошибка: ' + error.message);
        }
    }
}

function closeEventModal() {
    document.getElementById('eventModal').style.display = 'none';
    document.getElementById('eventForm').reset();
    document.getElementById('editEventId').value = '';
}

// ---- Остальные функции (задачи, статистика, редактирование, удаление) ----
function extractTime(isoString) {
    const date = new Date(isoString);
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

function getPriorityClass(priority) {
    switch(priority) {
        case 'Низкая': return 'priority priority-low';
        case 'Средняя': return 'priority priority-medium';
        case 'Высокая': return 'priority priority-high';
        case 'Очень высокая': return 'priority priority-very-high';
        default: return 'priority priority-medium';
    }
}

async function toggleTaskStatus(taskId, currentStatus, event) {
    event.stopPropagation();
    try {
        const response = await fetch(`/api/tasks/${taskId}/status?is_completed=${!currentStatus}`, { method: 'PUT' });
        if (response.ok) {
            await loadTasksForCurrentDate();
            await loadTasksForWeek();
        }
    } catch (error) { console.error(error); }
}

async function deleteTask(taskId, event) {
    event.stopPropagation();
    if (confirm('Удалить задачу?')) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
            if (response.ok) {
                await loadTasksForCurrentDate();
                await loadTasksForWeek();
            } else alert('Ошибка удаления');
        } catch (error) { alert('Ошибка: ' + error.message); }
    }
}

async function editTask(taskId, event) {
    event.stopPropagation();
    try {
        const response = await fetch(`/api/tasks?start_date=${formatYMD(currentDate)}&end_date=${formatYMD(currentDate)}`);
        const tasks = await response.json();
        const task = tasks.find(t => t.id === taskId);
        if (task) {
            document.getElementById('modalTitle').innerText = 'Редактировать задачу';
            document.getElementById('taskName').value = task.name;
            const datePart = task.start_time.split('T')[0];
            const startTimePart = task.start_time.split('T')[1].slice(0,5);
            const endTimePart = task.end_time.split('T')[1].slice(0,5);
            document.getElementById('taskDate').value = datePart;
            document.getElementById('taskStartTime').value = startTimePart;
            document.getElementById('taskEndTime').value = endTimePart;
            document.getElementById('taskCategory').value = (task.category === 'Не указана') ? '' : task.category;
            document.getElementById('taskPriority').value = task.priority;
            document.getElementById('editTaskId').value = task.id;
            document.getElementById('taskModal').style.display = 'flex';
        }
    } catch (error) { alert('Не удалось загрузить задачу'); }
}

function displayTasks(tasksList) {
    const container = document.getElementById('tasks-container');
    container.innerHTML = '';
    for (const task of tasksList) {
        const card = document.createElement('div');
        card.className = 'task-card';
        if (task.is_completed) card.classList.add('completed');
        const startTime = extractTime(task.start_time);
        const endTime = extractTime(task.end_time);
        const timeRange = `${startTime} - ${endTime}`;
        const priorityClass = getPriorityClass(task.priority);
        let categoryHtml = '';
        if (task.category !== 'Не указана') categoryHtml = `<span class="category">${escapeHtml(task.category)}</span>`;

        card.innerHTML = `
            <div class="task-header">
                <div class="task-title">${escapeHtml(task.name)}</div>
                <div class="task-actions">
                    <button class="edit-task" data-id="${task.id}" title="Редактировать">✏️</button>
                    <button class="delete-task" data-id="${task.id}" title="Удалить">🗑️</button>
                    <input type="checkbox" class="custom-checkbox" ${task.is_completed ? 'checked' : ''}
                           onchange="toggleTaskStatus(${task.id}, ${task.is_completed}, event)">
                </div>
            </div>
            <div class="task-details">
                <span class="time-range">${timeRange}</span>
                <span class="duration"> ⏱ ${task.duration} мин</span>
                ${categoryHtml}
                <div style="flex:1"></div>
                <span class="${priorityClass}">${escapeHtml(task.priority)}</span>
            </div>
        `;
        container.appendChild(card);
    }
    document.querySelectorAll('.edit-task').forEach(btn => {
        const id = parseInt(btn.dataset.id);
        btn.addEventListener('click', (e) => editTask(id, e));
    });
    document.querySelectorAll('.delete-task').forEach(btn => {
        const id = parseInt(btn.dataset.id);
        btn.addEventListener('click', (e) => deleteTask(id, e));
    });
}

function updateStats(tasksList) {
    const total = tasksList.length;
    const completed = tasksList.filter(t => t.is_completed).length;
    document.getElementById('total-count').innerText = total;
    document.getElementById('completed-count').innerText = completed;
    document.getElementById('pending-count').innerText = total - completed;
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>]/g, function(m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
}

async function saveTask(event) {
    event.preventDefault();
    const name = document.getElementById('taskName').value.trim();
    const dateStr = document.getElementById('taskDate').value;
    const startTimeStr = document.getElementById('taskStartTime').value;
    const endTimeStr = document.getElementById('taskEndTime').value;
    const category = document.getElementById('taskCategory').value.trim() || 'Не указана';
    const priority = document.getElementById('taskPriority').value;
    const editId = document.getElementById('editTaskId').value;

    if (!name || !dateStr || !startTimeStr || !endTimeStr) {
        alert('Заполните название, дату и время начала/конца');
        return;
    }
    const startDateTime = `${dateStr}T${startTimeStr}:00`;
    const endDateTime = `${dateStr}T${endTimeStr}:00`;

    const payload = {
        name: name,
        start_time: startDateTime,
        end_time: endDateTime,
        category: category,
        priority: priority,
        is_completed: false
    };

    try {
        let url = '/api/tasks', method = 'POST';
        if (editId) {
            url = `/api/tasks/${editId}`;
            method = 'PUT';
        }
        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (response.ok) {
            closeModal();
            await loadTasksForCurrentDate();
            await loadTasksForWeek();
        } else {
            const err = await response.json();
            alert('Ошибка сохранения: ' + JSON.stringify(err));
        }
    } catch (error) {
        alert('Ошибка соединения: ' + error.message);
    }
}

function closeModal() {
    document.getElementById('taskModal').style.display = 'none';
    document.getElementById('taskForm').reset();
    document.getElementById('editTaskId').value = '';
    document.getElementById('modalTitle').innerText = 'Новая задача';
    document.getElementById('taskDate').value = formatYMD(currentDate);
}

// ---- Глобальные переменные для дедлайнов ----
let allDeadlines = [];

// ---- Загрузка дедлайнов (всех, но с сортировкой) ----
async function loadDeadlines() {
    try {
        const res = await fetch('/api/deadlines/all');  // или /active? нужно видеть и выполненные для сортировки
        if (!res.ok) throw new Error();
        let deadlines = await res.json();
        // сортируем: сначала невыполненные, потом выполненные
        deadlines.sort((a, b) => a.is_completed - b.is_completed);
        allDeadlines = deadlines;
        renderDeadlines();
        renderCalendar();  // обновим оранжевые точки
    } catch (error) {
        console.error('Ошибка загрузки дедлайнов', error);
    }
}

// ---- Отрисовка дедлайнов с фитильком ----
function renderDeadlines() {
    const container = document.getElementById('deadlinesList');
    if (!allDeadlines.length) {
        container.innerHTML = '<div class="no-deadlines">Нет активных дедлайнов</div>';
        return;
    }
    const now = new Date();
    container.innerHTML = allDeadlines.map(deadline => {
        const created = new Date(deadline.created_at);
        const deadlineTime = new Date(deadline.deadline_time);
        let percentRemaining = 0;
        let isExpired = false;
        let fuseClass = '';
        if (!deadline.is_completed) {
    if (now >= deadlineTime) {
        isExpired = true;
        percentRemaining = 0;
        fuseClass = '';
    } else if (deadlineTime > created) {
        const total = deadlineTime - created;
        const elapsed = now - created;
        let remaining = (total - elapsed) / total * 100;
        remaining = Math.min(100, Math.max(0, remaining));
        percentRemaining = Math.floor(remaining);
    }
} else {
    percentRemaining = 100;
    fuseClass = 'completed-fuse';
}
        const bombIcon = isExpired ? '💥' : '💣';
        const expiredClass = isExpired ? 'deadline-expired' : '';
        return `
            <div class="deadline-item ${deadline.is_completed ? 'completed-deadline' : ''} ${expiredClass}"
                 data-id="${deadline.id}"
                 data-created="${deadline.created_at}"
                 data-deadline="${deadline.deadline_time}">
                <div class="deadline-header">
                    <span class="deadline-name">${escapeHtml(deadline.name)}</span>
                    <div class="deadline-actions">
                        <button class="edit-deadline" data-id="${deadline.id}" title="Редактировать">✏️</button>
                        <button class="delete-deadline" data-id="${deadline.id}" title="Удалить">🗑️</button>
                        <input type="checkbox" class="deadline-checkbox" ${deadline.is_completed ? 'checked' : ''}
                               data-id="${deadline.id}" onchange="toggleDeadlineStatus(this)">
                    </div>
                </div>
                <div class="deadline-fuse">
                    <span class="bomb-icon">${bombIcon}</span>
                    <div class="fuse-bar">
                        <div class="fuse-progress ${fuseClass}" style="width: ${percentRemaining}%;"></div>
                    </div>
                </div>
                <div class="deadline-time">
                    Сгорает: ${deadlineTime.toLocaleString('ru-RU')}
                </div>
            </div>
        `;
    }).join('');

    attachDeadlineHandlers();
}

async function toggleDeadlineStatus(checkbox) {
    const deadlineId = parseInt(checkbox.dataset.id);
    const isCompleted = checkbox.checked;
    await fetch(`/api/deadlines/${deadlineId}/status?is_completed=${isCompleted}`, { method: 'PUT' });
    await loadDeadlines();
}

function attachDeadlineHandlers() {
    document.querySelectorAll('.edit-deadline').forEach(btn => {
        btn.onclick = () => openDeadlineModal(parseInt(btn.dataset.id));
    });
    document.querySelectorAll('.delete-deadline').forEach(btn => {
        btn.onclick = async () => {
            if (confirm('Удалить дедлайн?')) {
                const id = parseInt(btn.dataset.id);
                await fetch(`/api/deadlines/${id}`, { method: 'DELETE' });
                await loadDeadlines();
            }
        };
    });
}

// ---- Таймер для плавного обновления ширины фитилька ----
function startDeadlineTimer() {
    setInterval(() => {
        document.querySelectorAll('.deadline-item:not(.completed-deadline)').forEach(item => {
            const created = new Date(item.dataset.created);
            const deadline = new Date(item.dataset.deadline);
            const now = new Date();
            let percent = 0;
            if (deadline > created) {
                const total = deadline - created;
                const elapsed = now - created;
                let remaining = (total - elapsed) / total * 100;
                remaining = Math.min(100, Math.max(0, remaining));
                percent = Math.floor(remaining);
            }
            const fuseBar = item.querySelector('.fuse-progress');
            if (fuseBar) fuseBar.style.width = `${percent}%`;
        });
    }, 1000);
}

// ---- Модалка для дедлайнов ----
function openDeadlineModal(deadlineId = null) {
    const modal = document.getElementById('deadlineModal');
    const form = document.getElementById('deadlineForm');
    form.reset();
    document.getElementById('editDeadlineId').value = '';
    document.getElementById('deadlineModalTitle').innerText = 'Новый дедлайн';
    if (deadlineId) {
        document.getElementById('deadlineModalTitle').innerText = 'Редактировать дедлайн';
        fetch(`/api/deadlines/all`)
            .then(res => res.json())
            .then(deadlines => {
                const dl = deadlines.find(d => d.id === deadlineId);
                if (dl) {
                    document.getElementById('deadlineName').value = dl.name;
                    document.getElementById('deadlineDateTime').value = dl.deadline_time.slice(0,16);
                    document.getElementById('editDeadlineId').value = dl.id;
                }
            });
    }
    modal.style.display = 'flex';
}

async function saveDeadline(event) {
    event.preventDefault();
    const name = document.getElementById('deadlineName').value.trim();
    const deadlineDateTime = document.getElementById('deadlineDateTime').value;
    const editId = document.getElementById('editDeadlineId').value;
    if (!name || !deadlineDateTime) {
        alert('Заполните название и дату/время');
        return;
    }
    const payload = { name, deadline_time: deadlineDateTime, is_completed: false };
    try {
        let url = '/api/deadlines', method = 'POST';
        if (editId) {
            url = `/api/deadlines/${editId}`;
            method = 'PUT';
        }
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            closeDeadlineModal();
            await loadDeadlines();
        } else {
            const err = await res.json();
            alert('Ошибка: ' + (err.detail || 'Не удалось сохранить дедлайн'));
        }
    } catch (error) {
        alert('Ошибка соединения: ' + error.message);
    }
}

function closeDeadlineModal() {
    document.getElementById('deadlineModal').style.display = 'none';
    document.getElementById('deadlineForm').reset();
    document.getElementById('editDeadlineId').value = '';
}

// ---- Инициализация ----
document.getElementById('openModalBtn').onclick = () => {
    closeModal();
    document.getElementById('taskModal').style.display = 'flex';
};
document.getElementById('closeModalBtn').onclick = closeModal;
window.onclick = (e) => { if (e.target === document.getElementById('taskModal')) closeModal(); };
document.getElementById('taskForm').onsubmit = saveTask;

document.getElementById('prevWeekBtn').onclick = prevWeek;
document.getElementById('nextWeekBtn').onclick = nextWeek;

document.getElementById('addEventBtn').onclick = () => openEventModal();
document.getElementById('closeEventModalBtn').onclick = closeEventModal;
window.onclick = (e) => { if (e.target === document.getElementById('eventModal')) closeEventModal(); };
document.getElementById('eventForm').onsubmit = saveEvent;

document.getElementById('addDeadlineBtn').onclick = () => openDeadlineModal();
document.getElementById('closeDeadlineModalBtn').onclick = closeDeadlineModal;
window.onclick = (e) => { if (e.target === document.getElementById('deadlineModal')) closeDeadlineModal(); };
document.getElementById('deadlineForm').onsubmit = saveDeadline;

// Запуск
loadWeekInfo().then(() => {
    loadTasksForWeek().then(() => {
        loadAllEventsForCalendar().then(() => {
            if (!currentDate) currentDate = new Date(displayedWeekStart);
            loadTasksForCurrentDate();
            loadEventsForDate(currentDate);
            loadDeadlines();
            startDeadlineTimer();
            loadProfile();
        });
    });
});



// ---- Профиль и выпадающее меню ----
const profileIcon = document.getElementById('profileIcon');
const profileDropdown = document.getElementById('profileDropdown');
const dropdownUsername = document.getElementById('dropdownUsername');
const dropdownLogoutBtn = document.getElementById('dropdownLogoutBtn');

// Загрузка профиля и обновление иконки
async function loadProfile() {
    try {
        const res = await fetch('/auth/me');
        if (!res.ok) {
            if (res.status === 401) window.location.href = '/login';
            return;
        }
        const user = await res.json();
        // Обновляем букву в кружке
        const firstLetter = user.username.charAt(0).toUpperCase();
        profileIcon.textContent = firstLetter;
        // Обновляем имя в выпадающем меню
        dropdownUsername.textContent = user.username;
    } catch (error) {
        console.error('Ошибка загрузки профиля', error);
    }
}

// Показ/скрытие выпадающего меню
if (profileIcon) {
    profileIcon.onclick = (e) => {
        e.stopPropagation();
        const isVisible = profileDropdown.style.display === 'block';
        profileDropdown.style.display = isVisible ? 'none' : 'block';
    };
}

// Закрытие при клике вне меню
document.addEventListener('click', (e) => {
    if (!profileIcon.contains(e.target) && !profileDropdown.contains(e.target)) {
        profileDropdown.style.display = 'none';
    }
});

// Выход из профиля
if (dropdownLogoutBtn) {
    dropdownLogoutBtn.onclick = async () => {
        await fetch('/auth/logout', { method: 'POST' });
        window.location.href = '/login';
    };
}