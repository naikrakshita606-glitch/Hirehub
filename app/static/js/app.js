document.addEventListener('DOMContentLoaded', function () {
  const searchForms = document.querySelectorAll('form');
  searchForms.forEach((form) => {
    if (form.querySelector('input[name="q"]')) {
      form.addEventListener('submit', function (event) {
        const queryInput = form.querySelector('input[name="q"]');
        if (queryInput && queryInput.value.trim() === '') {
          event.preventDefault();
        }
      });
    }
  });
});
