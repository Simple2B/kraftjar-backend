// search flow
const searchInput: HTMLInputElement = document.querySelector(
  '#table-search-services',
);
const searchInputButton = document.querySelector(
  '#table-search-service-button',
);
if (searchInputButton && searchInput) {
  searchInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchInput.value);
    window.location.href = `${url.href}`;
  });
}
