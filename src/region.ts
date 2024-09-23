// search flow
const searchRegionInput: HTMLInputElement = document.querySelector(
  '#table-search-regions',
);
const searchRegionInputButton = document.querySelector(
  '#table-search-region-button',
);
if (searchRegionInputButton && searchRegionInput) {
  searchRegionInputButton.addEventListener('click', () => {
    const url = new URL(window.location.href);
    url.searchParams.set('q', searchRegionInput.value);
    window.location.href = `${url.href}`;
  });
}
