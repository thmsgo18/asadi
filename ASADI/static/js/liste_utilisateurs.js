// Récupère un cookie par son nom
function getCookie(name) {
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) {
            return decodeURIComponent(c.slice(name.length + 1));
        }
    }
    return null;
}

// Définition des fonctions en dehors du DOMContentLoaded pour la portée globale
function setNiveau(barWrapper, valeur, max) {
    const bar = barWrapper.querySelector('.progress-bar');
    const pourcentage = (valeur / max) * 100;

    if (pourcentage > 60) {
        bar.style.backgroundColor = '#06c5bd';
        barWrapper.style.backgroundColor = '#87ccc4';
    } else if (pourcentage > 30) {
        bar.style.backgroundColor = '#FFB347';
        barWrapper.style.backgroundColor = '#d1a879';
    } else {
        bar.style.backgroundColor = '#D94352';
        barWrapper.style.backgroundColor = '#c8949b';
    }
}

// Définition des fonctions directement sur l'objet window pour être accessibles partout
window.openEditModal = function(btn) {
    console.log('openEditModal appelé avec:', btn);
    console.log('Dataset du bouton:', btn.dataset);
    
    try {
        // 1) on récupère la modal et le formulaire
        const modal = document.getElementById('editModal');
        console.log('Modal trouvée:', modal);
        
        if (!modal) {
            console.error('La modal #editModal est introuvable dans le DOM!');
            return;
        }
        
        const form = document.getElementById('edit-form');
        console.log('Formulaire trouvé:', form);
        
        if (!form) {
            console.error('Le formulaire #edit-form est introuvable dans le DOM!');
            return;
        }
        
        // 2) on vérifie chaque élément avant de l'utiliser
        const userIdInput = document.getElementById('modal-user-id');
        const usernameInput = document.getElementById('edit-username');
        const prenomInput = document.getElementById('edit-prenom');
        const nomInput = document.getElementById('edit-nom');
        const emailInput = document.getElementById('edit-email');
        const niveauInput = document.getElementById('edit-niveau');
        
        console.log('Champs trouvés:', {
            userIdInput,
            usernameInput,
            prenomInput,
            nomInput,
            emailInput,
            niveauInput
        });
        
        // Vérification des éléments manquants
        if (!userIdInput) console.error('Champ #modal-user-id introuvable!');
        if (!usernameInput) console.error('Champ #edit-username introuvable!');
        if (!prenomInput) console.error('Champ #edit-prenom introuvable!');
        if (!nomInput) console.error('Champ #edit-nom introuvable!');
        if (!emailInput) console.error('Champ #edit-email introuvable!');
        if (!niveauInput) console.error('Champ #edit-niveau introuvable!');
        
        // Remplissage des champs s'ils existent
        if (userIdInput) userIdInput.value = btn.dataset.id;
        if (usernameInput) usernameInput.value = btn.dataset.username;
        if (prenomInput) prenomInput.value = btn.dataset.prenom;
        if (nomInput) nomInput.value = btn.dataset.nom;
        if (emailInput) emailInput.value = btn.dataset.email;
        if (niveauInput) niveauInput.value = btn.dataset.niveau;

        // 3) on adapte l'URL d'action du form si tout est OK
        if (form && btn.dataset.id) {
            console.log('URL du formulaire avant:', form.action);
            form.action = form.action.replace('/0/', `/${btn.dataset.id}/`);
            console.log('URL du formulaire après:', form.action);
        }

        // 4) on affiche la modal si elle existe
        if (modal) {
            modal.style.display = 'block';
            console.log('Modal affichée avec succès');
        }
    } catch (error) {
        console.error('Erreur dans openEditModal:', error);
    }
};

window.fermerEditModal = function() {
    const modal = document.getElementById("editModal");
    if (modal) {
        modal.style.display = "none";
        console.log('Modal fermée avec succès');
    } else {
        console.error('Modal #editModal introuvable lors de la fermeture!');
    }
    const url = new URL(window.location);
    url.searchParams.delete("open");
    url.searchParams.delete("msg");
    window.history.replaceState({}, document.title, url.toString());
};

document.addEventListener("DOMContentLoaded", () => {
    const csrftoken  = getCookie('csrftoken');
    const url        = window.SUPPRESSION_URL;
    const noProfile  = document.getElementById('aucun-profil');
    const statsSec   = document.getElementById('stats-container');
    const toggleBtn  = document.getElementById('toggle-stats');
    const searchInput= document.getElementById("search-user");
    const userItems  = document.querySelectorAll(".user-item");

    // Les fonctions openEditModal et fermerEditModal sont maintenant définies globalement
    // en dehors du bloc DOMContentLoaded pour être disponibles immédiatement

    // Recherche en temps réel
    searchInput.addEventListener("input", () => {
        const q = searchInput.value.trim().toLowerCase();
        userItems.forEach(item => {
            const name = item.dataset.name.toLowerCase();
            item.style.display = name.includes(q) ? "flex" : "none";
        });
    });

    // Affiche un profil et masque stats + message
    window.afficherProfilUtilisateur = id => {
        document.querySelectorAll('.user-profile').forEach(div => div.style.display = 'none');
        if (statsSec) statsSec.style.display = 'none';
        const prof = document.getElementById(`profil-utilisateur-${id}`);
        if (prof) {
            prof.style.display = 'block';
            noProfile.style.display = 'none';
        } else {
            noProfile.style.display = 'block';
        }
    };

    // Basculer l'affichage des stats
    toggleBtn.addEventListener('click', () => {
        // masque tous les profils
        document.querySelectorAll('.user-profile').forEach(div => div.style.display = 'none');
        noProfile.style.display = 'none';
        if (statsSec.style.display === 'block') {
            statsSec.style.display = 'none';
            noProfile.style.display = 'block';
            toggleBtn.textContent = 'Afficher les statistiques';
        } else {
            statsSec.style.display = 'block';
            toggleBtn.textContent = 'Masquer les statistiques';
        }
    });

    // Confirmation et suppression AJAX
    document.querySelectorAll(".btn-asadi.danger").forEach(btn => {
        btn.addEventListener("click", e => {
            e.preventDefault();
            const userId   = btn.dataset.id;
            const fullName = btn.dataset.name;
            if (!confirm(`⚠️ Confirmez-vous la suppression de ${fullName} ?`)) return;

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "Content-Type": "application/x-www-form-urlencoded"
                },
                body: new URLSearchParams({ user_id: userId }).toString()
            })
            .then(r => {
                if (!r.ok) throw new Error(`Status ${r.status}`);
                return r.json();
            })
            .then(data => {
                if (data.success) {
                    // retire l'item et le profil ouvert
                    const row    = document.getElementById(`user-row-${userId}`);
                    const profEl = document.getElementById(`profil-utilisateur-${userId}`);
                    if (row) row.remove();
                    if (profEl) profEl.style.display = 'none';
                    noProfile.style.display = 'block';
                } else {
                    alert("Erreur : " + data.error);
                }
            })
            .catch(err => {
                console.error("fetch error:", err);
                alert("Erreur réseau ou CSRF invalide, suppression impossible.");
            });
        });
    }); 

    // Gestion des boutons d'édition
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', e => {
            e.preventDefault();
            window.openEditModal(btn);
        });
    });

    // Fermer la modal si clic en dehors de la fenêtre
    window.onclick = function(event) {
        const modal = document.getElementById("editModal");
        if (event.target === modal) {
            window.fermerEditModal();
        }
    };

    // Gestion de la barre de niveau pour chaque profil
    document.querySelectorAll('.user-profile').forEach(profileEl => {
        const valeur = parseInt(profileEl.dataset.niveau, 10);
        const max    = parseInt(profileEl.dataset.max, 10);
        const wrapper = profileEl.querySelector('.progress-bar-wrapper');
        if (wrapper && !isNaN(valeur) && !isNaN(max)) {
            setNiveau(wrapper, valeur, max);
        }
    });
});