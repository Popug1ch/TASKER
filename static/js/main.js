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

        const dayCard = document.createElement('div');
        dayCard.className = 'day-card';
        if (formatYMD(currentDate) === ymd) dayCard.classList.add('active');
        dayCard.innerHTML = `
            ${hasEvent ? '<span class="event-dot"></span>' : ''}
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

// События
document.getElementById('addEventBtn').onclick = () => openEventModal();
document.getElementById('closeEventModalBtn').onclick = closeEventModal;
window.onclick = (e) => { if (e.target === document.getElementById('eventModal')) closeEventModal(); };
document.getElementById('eventForm').onsubmit = saveEvent;

// Запуск
loadWeekInfo().then(() => {
    loadTasksForWeek().then(() => {
        loadAllEventsForCalendar().then(() => {
            if (!currentDate) currentDate = new Date(displayedWeekStart);
            loadTasksForCurrentDate();
            loadEventsForDate(currentDate);
        });
    });
});