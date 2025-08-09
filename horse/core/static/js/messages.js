function updateUnreadCount() {
    const branchName = document.body.dataset.branch;
    fetch(`/api/messages/unread-count/${branchName}/`)
        .then(response => response.json())
        .then(data => {
            const counter = document.getElementById('unread-message-count');
            if (counter) {
                counter.textContent = data.count;
                counter.style.display = data.count > 0 ? 'block' : 'none';
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    updateUnreadCount();
    setInterval(updateUnreadCount, 60000);
});