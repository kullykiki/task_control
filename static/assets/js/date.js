document.addEventListener('DOMContentLoaded', function() {
    const currentWeekElement = document.querySelector('.current-week');
    const monthSelect = document.querySelector('.month-select');
    const yearSelect = document.querySelector('.year-select');
    const prevWeekBtn = document.querySelector('.prev.week-btn');
    const nextWeekBtn = document.querySelector('.next.week-btn');
    const todayBtn = document.querySelector('.today-btn');
    const calendarDays = document.querySelector('.calendar-days');

    let currentDate = new Date();

    // Populate year select
    const currentYear = currentDate.getFullYear();
    for (let i = currentYear - 5; i <= currentYear + 5; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = i;
        yearSelect.appendChild(option);
    }
    yearSelect.value = currentYear;
    monthSelect.value = currentDate.getMonth();

    function getStartOfWeek(date) {
        const day = date.getDay();
        const diff = date.getDate() - day + (day === 0 ? -6 : 1);
        return new Date(date.setDate(diff));
    }

    function getEndOfWeek(date) {
        const start = getStartOfWeek(new Date(date));
        return new Date(start.getFullYear(), start.getMonth(), start.getDate() + 6);
    }

    function renderWeek() {
        calendarDays.innerHTML = '';
        let start = getStartOfWeek(new Date(currentDate));
        let end = getEndOfWeek(new Date(currentDate));

        currentWeekElement.textContent = `${start.toLocaleDateString()} - ${end.toLocaleDateString()}`;

        const today = new Date();
        for (let i = 0; i < 7; i++) {
            const dayElement = document.createElement('div');
            dayElement.classList.add('calendar-day');
            dayElement.textContent = start.getDate();
            if (start.toDateString() === today.toDateString()) {
                dayElement.classList.add('today');
            }
            calendarDays.appendChild(dayElement);
            start.setDate(start.getDate() + 1);
        }
    }

    prevWeekBtn.addEventListener('click', function() {
        currentDate.setDate(currentDate.getDate() - 7);
        renderWeek();
    });

    nextWeekBtn.addEventListener('click', function() {
        currentDate.setDate(currentDate.getDate() + 7);
        renderWeek();
    });

    todayBtn.addEventListener('click', function() {
        currentDate = new Date();
        monthSelect.value = currentDate.getMonth();
        yearSelect.value = currentDate.getFullYear();
        renderWeek();
    });

    monthSelect.addEventListener('change', function() {
        currentDate.setMonth(monthSelect.value);
        renderWeek();
    });

    yearSelect.addEventListener('change', function() {
        currentDate.setFullYear(yearSelect.value);
        renderWeek();
    });

    renderWeek();
});
