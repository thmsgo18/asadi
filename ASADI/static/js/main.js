// main.js
document.addEventListener('DOMContentLoaded', () => {
  // ————————— Drag & Drop Upload —————————
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const fileList = document.getElementById('file-list');
  let filesBuffer = [];

  dropZone.addEventListener('click', () => fileInput.click());
  dropZone.addEventListener('dragover', e => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });
  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });
  dropZone.addEventListener('drop', e => {
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
      btn.addEventListener('click', e => {
        e.stopPropagation();
        const idx = +e.target.getAttribute('data-index');
        filesBuffer.splice(idx, 1);
        renderFileList();
        updateInputFiles();
      });
    });
  }

  function updateInputFiles() {
    const dt = new DataTransfer();
    filesBuffer.forEach(f => dt.items.add(f));
    fileInput.files = dt.files;
  }

  console.log("💾 Drag & Drop + suppression des fichiers : PRÊT ✅");

  // ————— Fermer le modal workspace si on clique à l’extérieur —————
  document.addEventListener('click', e => {
    const modal = document.getElementById('workspace-form-wrapper');
    if (!modal.contains(e.target) && !e.target.classList.contains('modify-button')) {
      modal.style.display = 'none';
    }
  });

  // ————— Upload AJAX avec spinner —————
  const form = document.getElementById('upload-form');

  form.addEventListener('submit', e => {
    e.preventDefault();
    // affiche l’overlay+spinner (doit être dans prompt.js)
    showLoadingOverlay();

    const data = new FormData(form);
    const csrftoken = form.querySelector('[name="csrfmiddlewaretoken"]').value;

    fetch(form.action, {
      method: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      body: data
    })
    .then(response => {
      if (!response.ok) throw new Error(`Statut ${response.status}`);
      return response.json();
    })
    .then(json => {
      hideLoadingOverlay();
      if (json.success) {
        alert('✅ Documents ingérés avec succès !');
        window.location.reload();
      } else {
        let errorMessage = '❌ Échec de l’ingestion.';
        if (json.error) {
          errorMessage += `\nErreur : ${json.error}`;
        }
        if (json.failed_files && Array.isArray(json.failed_files)) {
          errorMessage += `\n\nFichiers échoués :\n` + json.failed_files.map(file => `• ${file}`).join('\n');
        }
        alert(errorMessage);
        window.location.reload();
      }
    })
    .catch(err => {
      hideLoadingOverlay();
      alert('❌ Erreur lors de l’envoi : ' + err);
      window.location.reload();
    });
  });

  // ————— Fonctions modal & workspace —————
  window.openWorkspaceForm = function(docId, currentWorkspaceName) {
    const modal = document.getElementById('workspace-form-wrapper');
    document.getElementById('doc-id-input').value = docId;
    const select = document.getElementById('workspace-select-modal');
    let matched = false;
    for (let opt of select.options) {
      if (opt.text === currentWorkspaceName) {
        opt.selected = true;
        matched = true;
        break;
      }
    }
    if (!matched) select.selectedIndex = 0;
    modal.style.display = 'flex';
  }

  window.closeWorkspaceForm = function() {
    document.getElementById('workspace-form-wrapper').style.display = 'none';
  }

  window.deleteWorkspace = function(mode) {
    const select = document.getElementById('workspace');
    const wsId = select.value;
    if (!wsId) return alert("Sélectionnez un workspace à supprimer.");
    const msg = mode === 'keep'
      ? "⚠️ Le workspace sera supprimé, mais les fichiers seront conservés. Continuer ?"
      : "⚠️ Tous les fichiers seront supprimés. Continuer ?";
    if (!confirm(msg)) return;
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/documents/delete-workspace/';
    const csrf = document.querySelector('[name=csrfmiddlewaretoken]').cloneNode();
    csrf.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const wsInput = document.createElement('input');
    wsInput.type = 'hidden'; wsInput.name = 'ws_id'; wsInput.value = wsId;
    const modeInput = document.createElement('input');
    modeInput.type = 'hidden'; modeInput.name = 'mode'; modeInput.value = mode;
    form.append(csrf, wsInput, modeInput);
    document.body.appendChild(form);
    form.submit();
  }
});