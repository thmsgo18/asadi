document.addEventListener('DOMContentLoaded', function () {
    // Drag & Drop Upload
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const fileList = document.getElementById('file-list');
    let filesBuffer = [];

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        addFilesToBuffer(e.dataTransfer.files);
    });

    fileInput.addEventListener('change', () => {
        addFilesToBuffer(fileInput.files);
    });

    function addFilesToBuffer(fileListInput) {
        for (let i = 0; i < fileListInput.length; i++) {
            filesBuffer.push(fileListInput[i]);
        }
        renderFileList();
        updateInputFiles();
    }

    function renderFileList() {
        fileList.innerHTML = '';
        filesBuffer.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.innerHTML = `
                ${file.name}
                <button data-index="${index}" class="delete-temp">Supprimer</button>
            `;
            fileList.appendChild(fileItem);
        });

        document.querySelectorAll('.delete-temp').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const index = e.target.getAttribute('data-index');
                filesBuffer.splice(index, 1);
                renderFileList();
                updateInputFiles();
            });
        });
    }

    function updateInputFiles() {
        const dataTransfer = new DataTransfer();
        filesBuffer.forEach(file => dataTransfer.items.add(file));
        fileInput.files = dataTransfer.files;
    }

    console.log("💾 Drag & Drop + suppression des fichiers : PRÊT ✅");

    document.addEventListener('click', function (e) {
        const form = document.getElementById('workspace-form-wrapper');
        if (!form.contains(e.target) && !e.target.classList.contains('modify-button')) {
            form.style.display = 'none';
        }
    });
});

function openWorkspaceForm(docId, currentWorkspaceName) {
    const modal = document.getElementById('workspace-form-wrapper');
    document.getElementById('doc-id-input').value = docId;

    const select = document.getElementById('workspace-select-modal');
    const options = select.options;

    let matched = false;
    for (let i = 0; i < options.length; i++) {
        const opt = options[i];
        if (opt.text === currentWorkspaceName) {
            opt.selected = true;
            matched = true;
            break;
        }
    }

    if (!matched || !currentWorkspaceName) {
        select.selectedIndex = 0;
    }

    modal.style.display = 'flex';
}

function closeWorkspaceForm() {
    const modal = document.getElementById('workspace-form-wrapper');
    modal.style.display = 'none';
}

function deleteWorkspace(mode) {
    const select = document.getElementById('workspace');
    const wsId = select.value;

    if (!wsId) return alert("Sélectionnez un workspace à supprimer.");

    const confirmMsg = mode === 'keep'
        ? "⚠️ Le workspace sera supprimé, mais les fichiers seront conservés dans le dossier général. Continuer ?"
        : "⚠️ Tous les fichiers de ce workspace seront supprimés définitivement. Continuer ?";

    if (!confirm(confirmMsg)) return;

    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/documents/delete-workspace/';  // adapte au bon chemin

    const csrf = document.querySelector('[name=csrfmiddlewaretoken]');
    const csrfClone = document.createElement('input');
    csrfClone.type = 'hidden';
    csrfClone.name = 'csrfmiddlewaretoken';
    csrfClone.value = csrf.value;

    const wsInput = document.createElement('input');
    wsInput.type = 'hidden';
    wsInput.name = 'ws_id';
    wsInput.value = wsId;

    const modeInput = document.createElement('input');
    modeInput.type = 'hidden';
    modeInput.name = 'mode';
    modeInput.value = mode;

    form.appendChild(csrfClone);
    form.appendChild(wsInput);
    form.appendChild(modeInput);
    document.body.appendChild(form);
    form.submit();
}