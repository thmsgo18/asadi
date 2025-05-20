function showLoadingOverlay() {
  document.getElementById('loading-overlay').style.display = 'flex';
}
function hideLoadingOverlay() {
  document.getElementById('loading-overlay').style.display = 'none';
}
window.showLoadingOverlay = showLoadingOverlay;
window.hideLoadingOverlay = hideLoadingOverlay;