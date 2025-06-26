document.addEventListener('DOMContentLoaded', () => {
    // --- Data Simulasi (Ganti ini dengan data dari backend sungguhan nanti) ---
    // Pastikan data ini persisten menggunakan localStorage
    let users = JSON.parse(localStorage.getItem('adminUsers')) || [
        { id: 'u1', username: 'Ujang', email: 'ujangke pasar123@gmail.com', status: 'On', ip: '123.4.56.789', isBackedUp: false }, // Tambahkan isBackedUp
        { id: 'u2', username: 'Siti', email: 'siti.aja@example.com', status: 'Off', ip: '192.168.1.10', isBackedUp: true },  // Contoh sudah di-backup
        { id: 'u3', username: 'Budi', email: 'budi.santoso@email.com', status: 'On', ip: '10.0.0.5', isBackedUp: false },
        { id: 'u4', username: 'Ani', email: 'ani.ceria@mail.net', status: 'Off', ip: '172.16.0.2', isBackedUp: true }   // Contoh sudah di-backup
    ];

    let totalJournals = parseInt(localStorage.getItem('totalJournals')) || 7;
    // totalBackedUp tidak perlu disimpan sebagai variabel terpisah, bisa dihitung dari `users`

    // Simpan data ke localStorage setiap kali ada perubahan
    const saveData = () => {
        localStorage.setItem('adminUsers', JSON.stringify(users));
        localStorage.setItem('totalJournals', totalJournals.toString());
        // totalBackedUp akan dihitung ulang setiap kali render
    };

    // --- Elemen DOM ---
    const userTableBody = document.getElementById('userTableBody');
    const searchInput = document.getElementById('searchInput');
    const totalUsersSpan = document.getElementById('totalUsers');
    const totalJournalsSpan = document.getElementById('totalJournals');
    const totalBackedUpSpan = document.getElementById('totalBackedUp'); // BARIS BARU INI

    // --- Fungsi Render Tabel ---
    const renderTable = (dataToRender = users) => {
        userTableBody.innerHTML = ''; // Kosongkan tabel sebelum merender ulang
        if (dataToRender.length === 0) {
            userTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 20px;">Tidak ada data ditemukan.</td></tr>';
            return;
        }

        dataToRender.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td>${user.status}</td>
                <td>${user.ip}</td>
                <td>
                    <div class="action-buttons">
                        <button class="action-btn restore" data-id="${user.id}"><i class="fas fa-undo-alt"></i> Restore</button>
                        <button class="action-btn backup ${user.isBackedUp ? 'backed-up' : ''}" data-id="${user.id}" ${user.isBackedUp ? 'disabled' : ''}>
                            <i class="fas fa-save"></i> ${user.isBackedUp ? 'Backed Up' : 'Backup'}
                        </button>
                        <button class="action-btn delete" data-id="${user.id}"><i class="fas fa-trash-alt"></i> Delete</button>
                    </div>
                </td>
            `;
            userTableBody.appendChild(row);
        });

        updateStats(); // Update statistik setelah tabel dirender
        addTableEventListeners(); // Tambahkan event listener setelah tombol-tombol dibuat
    };

    // --- Fungsi Update Statistik ---
    const updateStats = () => {
        totalUsersSpan.textContent = users.length;
        totalJournalsSpan.textContent = totalJournals;
        const backedUpCount = users.filter(user => user.isBackedUp).length;
        totalBackedUpSpan.textContent = backedUpCount; // BARIS BARU INI
        saveData();
    };

    // --- Event Listeners untuk Tombol Aksi Tabel ---
    const addTableEventListeners = () => {
        document.querySelectorAll('.action-btn').forEach(button => {
            button.removeEventListener('click', handleActionButtonClick); // Hapus listener lama jika ada
            button.addEventListener('click', handleActionButtonClick);
        });
    };

    const handleActionButtonClick = (e) => {
        const button = e.currentTarget;
        const userId = button.dataset.id;
        const actionType = button.classList[1]; // restore, backup, delete

        const userIndex = users.findIndex(u => u.id === userId);
        if (userIndex === -1) {
            alert('Pengguna tidak ditemukan!');
            return;
        }

        const username = users[userIndex].username;

        switch (actionType) {
            case 'restore':
                if (confirm(`Apakah Anda yakin ingin melakukan Restore data untuk ${username}?`)) {
                    alert(`Data ${username} berhasil di-Restore! (Simulasi)`);
                    // Logika restore sebenarnya akan berkomunikasi dengan backend
                    // Jika restore berarti status isBackedUp kembali false
                    users[userIndex].isBackedUp = false; // Update status
                    renderTable(); // Render ulang tabel untuk update tombol
                }
                break;
            case 'backup':
                if (confirm(`Apakah Anda yakin ingin melakukan Backup data untuk ${username}?`)) {
                    alert(`Data ${username} berhasil di-Backup! (Simulasi)`);
                    users[userIndex].isBackedUp = true; // Set status menjadi backed up
                    renderTable(); // Render ulang tabel untuk update tombol
                }
                break;
            case 'delete':
                if (confirm(`Apakah Anda yakin ingin menghapus pengguna ${username}? Tindakan ini tidak dapat dibatalkan!`)) {
                    users.splice(userIndex, 1); // Hapus pengguna dari array
                    totalJournals = Math.max(0, totalJournals - 1); // Kurangi total jurnal (contoh saja)
                    alert(`Pengguna ${username} berhasil dihapus! (Simulasi)`);
                    renderTable(); // Render ulang tabel
                }
                break;
            default:
                console.log('Aksi tidak dikenali:', actionType);
        }
        saveData(); // Simpan perubahan setelah aksi
    };

    // --- Event Listener untuk Search ---
    searchInput.addEventListener('keyup', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filteredUsers = users.filter(user =>
            user.username.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm) ||
            user.ip.toLowerCase().includes(searchTerm) ||
            user.status.toLowerCase().includes(searchTerm)
        );
        renderTable(filteredUsers);
    });

    // --- Inisialisasi Saat Halaman Dimuat ---
    renderTable(); // Render tabel pertama kali
    updateStats(); // Update statistik saat pertama kali dimuat
});