// search flow
const searchServiceInput: HTMLInputElement = document.querySelector(
  '#table-search-services',
);
const searchServiceInputButton = document.querySelector(
  '#table-search-service-button',
);
if (searchServiceInputButton && searchServiceInput) {
  searchServiceInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchServiceInput.value);
    window.location.href = `${url.href}`;
  });
}
