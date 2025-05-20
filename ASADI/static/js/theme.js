const universiteCssUrl = "/static/css/general/universite.css"; // Chemin absolu correct

document.addEventListener('DOMContentLoaded', () => {
  const currentTheme = localStorage.getItem('theme') || 'default';

  let themeLink = document.getElementById('theme-colors');
  if (!themeLink) {
    themeLink = document.createElement('link');
    themeLink.rel = 'stylesheet';
    themeLink.id = 'theme-colors';
    document.head.appendChild(themeLink);
  }

  if (currentTheme === 'universite') {
    themeLink.href = universiteCssUrl;
  } else {
    themeLink.href = '';
  }

  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      const newTheme = (localStorage.getItem('theme') || 'default') === 'default' ? 'universite' : 'default';
      localStorage.setItem('theme', newTheme);

      if (newTheme === 'universite') {
        themeLink.href = universiteCssUrl;
      } else {
        themeLink.href = '';
      }

      location.reload(); // Recharge pour appliquer sans flash
    });
  }
});