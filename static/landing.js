document.addEventListener('DOMContentLoaded', () => {
    const appContainer = document.getElementById('app-container');
    const homeBtn = document.getElementById('homeBtn');
    const addEntriesBtn = document.getElementById('addEntriesBtn');
    const loginBtn = document.getElementById('loginBtn');
    const signUpBtn = document.getElementById('signUpBtn');
    const profileIcon = document.getElementById('profileIcon');

    let currentEditEntryId = null; // Untuk melacak entri yang sedang diedit

    // Fungsi untuk mendapatkan entri dari localStorage
    const getEntries = () => {
        const entries = JSON.parse(localStorage.getItem('tickieEntries')) || [];
        return entries.sort((a, b) => a.id - b.id); // Urutkan berdasarkan ID
    };

    // Fungsi untuk menyimpan entri ke localStorage
    const saveEntries = (entries) => {
        localStorage.setItem('tickieEntries', JSON.stringify(entries));
    };

    // Render Halaman 

    const renderLandingPage = () => {
        appContainer.innerHTML = `
            <div class="landing-page">
                <h1>Mulai hari dengan aksi<br><span>Tutup dengan catatan.</span></h1>
                <p>Jejak aktivitas harianmu, tersimpan dengan rapi.</p>
                <button id="getStartedNowBtn" class="primary-button">Get Started now</button>
            </div>
        `;

        // Sembunyikan/tampilkan tombol navigasi yang sesuai
        homeBtn.style.display = 'none';
        addEntriesBtn.style.display = 'none';
        loginBtn.style.display = 'inline-flex';
        signUpBtn.style.display = 'inline-flex';
        profileIcon.style.display = 'none';

        document.getElementById('getStartedNowBtn').addEventListener('click', () => {

            // Untuk demo, langsung ke halaman entries setelah "Get Started"
            // Di aplikasi nyata, ini akan ke login/signup
            isLoggedIn(true); // Simulasi login
            renderAllEntriesPage();
        });
    };

    const renderAllEntriesPage = () => {
        const entries = getEntries();
        let entriesHtml = '';
        if (entries.length === 0) {
            entriesHtml = '<p style="text-align: center; margin-top: 2rem; color: var(--secondary-color);">Belum ada entri. Yuk, tambahkan yang pertama!</p>';
        } else {
            entriesHtml = `
                <div class="entries-grid">
                    ${entries.map(entry => `
                        <div class="entry-card">
                            <div class="entry-id">ID: ${entry.id}</div>
                            <h3>${entry.title}</h3>
                            <p class="entry-description">${entry.description}</p>
                            <div class="actions">
                                <button class="action-button update-button" data-id="${entry.id}">Update</button>
                                <button class="action-button delete-button" data-id="${entry.id}">Delete</button>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        appContainer.innerHTML = `
            <div class="all-entries-container">
                <h2>All Entries</h2>
                ${entriesHtml}
            </div>
        `;

        // Tampilkan/sembunyikan tombol navigasi yang sesuai
        homeBtn.style.display = 'inline-flex';
        addEntriesBtn.style.display = 'inline-flex';
        loginBtn.style.display = 'none';
        signUpBtn.style.display = 'none';
        profileIcon.style.display = 'inline-flex';

        // Tambahkan event listener untuk tombol update dan delete
        document.querySelectorAll('.update-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const id = parseInt(e.target.dataset.id);
                const entryToEdit = entries.find(entry => entry.id === id);
                if (entryToEdit) {
                    renderAddEntryPage(entryToEdit);
                }
            });
        });

        document.querySelectorAll('.delete-button').forEach(button => {
            button.addEventListener('click', (e) => {
                const id = parseInt(e.target.dataset.id);
                deleteEntry(id);
            });
        });
    };

    const renderAddEntryPage = (entryToEdit = null) => {
        currentEditEntryId = entryToEdit ? entryToEdit.id : null;
        const title = entryToEdit ? entryToEdit.title : '';
        const description = entryToEdit ? entryToEdit.description : '';
        const submitText = entryToEdit ? 'Update Entry' : 'Submit';

        appContainer.innerHTML = `
            <div class="add-entry-container">
                <h2>${entryToEdit ? 'Edit Entry' : 'Add Entry'}</h2>
                <form id="entryForm">
                    <div class="form-group">
                        <label for="title">Title</label>
                        <input type="text" id="title" value="${title}" required>
                    </div>
                    <div class="form-group">
                        <label for="description">Description</label>
                        <textarea id="description" required>${description}</textarea>
                    </div>
                    <button type="submit" class="primary-button">${submitText}</button>
                </form>
            </div>
        `;

        // Tampilkan/sembunyikan tombol navigasi yang sesuai
        homeBtn.style.display = 'inline-flex';
        addEntriesBtn.style.display = 'inline-flex';
        loginBtn.style.display = 'none';
        signUpBtn.style.display = 'none';
        profileIcon.style.display = 'inline-flex';

        // Tambahkan event listener untuk form submit
        document.getElementById('entryForm').addEventListener('submit', (e) => {
            e.preventDefault();
            const newTitle = document.getElementById('title').value;
            const newDescription = document.getElementById('description').value;

            if (currentEditEntryId) {
                updateEntry(currentEditEntryId, newTitle, newDescription);
            } else {
                addEntry(newTitle, newDescription);
            }
        });
    };

    // Fungsi CRUD Entri 
    const addEntry = (title, description) => {
        const entries = getEntries();
        const newId = entries.length > 0 ? Math.max(...entries.map(e => e.id)) + 1 : 1;
        const newEntry = { id: newId, title, description };
        entries.push(newEntry);
        saveEntries(entries);
        renderAllEntriesPage(); // Kembali ke halaman semua entri
    };

    const updateEntry = (id, newTitle, newDescription) => {
        let entries = getEntries();
        entries = entries.map(entry =>
            entry.id === id ? { ...entry, title: newTitle, description: newDescription } : entry
        );
        saveEntries(entries);
        currentEditEntryId = null; // Reset edit ID
        renderAllEntriesPage(); // Kembali ke halaman semua entri
    };

    const deleteEntry = (id) => {
        if (confirm('Apakah Anda yakin ingin menghapus entri ini?')) {
            let entries = getEntries();
            entries = entries.filter(entry => entry.id !== id);
            saveEntries(entries);
            renderAllEntriesPage(); // Render ulang halaman setelah penghapusan
        }
    };

    // Simulasi Login/Status Pengguna 
    const isLoggedIn = (status) => {
        localStorage.setItem('isLoggedIn', status);
    };

    const checkLoginStatus = () => {
        return localStorage.getItem('isLoggedIn') === 'true';
    };

    // Event Listener Navigasi Global
    homeBtn.addEventListener('click', () => {
        if (checkLoginStatus()) {
            renderAllEntriesPage();
        } else {
            renderLandingPage();
        }
    });
    
    addEntriesBtn.addEventListener('click', () => {
        if (checkLoginStatus()) {
            renderAddEntryPage();
        } else {
            alert('Silakan login terlebih dahulu.');
            renderLandingPage();
        }
    });

    loginBtn.addEventListener('click', () => {
        isLoggedIn(true); // Simulasi login berhasil
        alert('Anda berhasil login!');
        renderAllEntriesPage();
    });

    signUpBtn.addEventListener('click', () => {
        isLoggedIn(true); // Simulasi signup berhasil
        alert('Pendaftaran berhasil! Anda sekarang login.');
        renderAllEntriesPage();
    });

    profileIcon.addEventListener('click', () => {
        if (confirm('Apakah Anda ingin logout?')) {
            isLoggedIn(false); // Simulasi logout
            alert('Anda telah logout.');
            renderLandingPage();
        }
    });


    // --- Inisialisasi Aplikasi ---
    // Tentukan halaman mana yang akan dirender saat pertama kali aplikasi dimuat
    if (checkLoginStatus()) {
        renderAllEntriesPage();
    } else {
        renderLandingPage();
    }
});