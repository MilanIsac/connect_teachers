document.addEventListener('DOMContentLoaded', () => {
    // --- SEARCH FUNCTIONALITY ---
    const input = document.getElementById('searchInput');
    const resultsBox = document.getElementById('searchResults');

    if (input && resultsBox) {
        input.addEventListener('input', async () => {
            const query = input.value.trim();

            if (query.length < 2) {
                resultsBox.style.display = 'none';
                resultsBox.innerHTML = '';
                return;
            }

            try {
                const res = await fetch(`/search_teachers?query=${encodeURIComponent(query)}`);
                const data = await res.json();

                if (data.length === 0) {
                    resultsBox.innerHTML = '<p class="m-0 text-muted small px-2">No results found</p>';
                    resultsBox.style.display = 'block';
                    return;
                }

                resultsBox.innerHTML = data.map(teacher => `
                    <a href="/profile/${teacher.username}" class="text-decoration-none text-dark small">
                        <div class="search-result py-1 px-2 border-bottom">
                            <strong class="small">${teacher.username}</strong><br>
                            <small>${teacher.description}</small>
                        </div>
                    </a>
                `).join('');

                resultsBox.style.display = 'block';
            } catch (err) {
                console.error('Search error:', err);
            }
        });

        // Hide results when clicking outside
        document.addEventListener('click', (e) => {
            if (!resultsBox.contains(e.target) && e.target !== input) {
                resultsBox.style.display = 'none';
            }
        });
    }

    // --- TYPING ANIMATION ---
    const text = "Welcome to Teacher's Connect";
    const target = document.getElementById("typing-title");
    const cursor = document.querySelector(".cursor");

    if (target) {
        let i = 0;
        function type() {
            if (i < text.length) {
                target.textContent += text.charAt(i);
                i++;
                setTimeout(type, 100);
            } else if (cursor) {
                cursor.style.display = 'none';
            }
        }
        type();
    }
});
