/******/ (() => { // webpackBootstrap
/*!***********************!*\
  !*** ./src/region.ts ***!
  \***********************/
// search flow
var searchRegionInput = document.querySelector('#table-search-regions');
var searchRegionInputButton = document.querySelector('#table-search-region-button');
if (searchRegionInputButton && searchRegionInput) {
    searchRegionInputButton.addEventListener('click', function () {
        var url = new URL(window.location.href);
        url.searchParams.set('q', searchRegionInput.value);
        window.location.href = "".concat(url.href);
    });
}

/******/ })()
;
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvcmVnaW9uLmpzIiwibWFwcGluZ3MiOiI7Ozs7QUFBQSxjQUFjO0FBQ2QsSUFBTSxpQkFBaUIsR0FBcUIsUUFBUSxDQUFDLGFBQWEsQ0FDaEUsdUJBQXVCLENBQ3hCLENBQUM7QUFDRixJQUFNLHVCQUF1QixHQUFHLFFBQVEsQ0FBQyxhQUFhLENBQ3BELDZCQUE2QixDQUM5QixDQUFDO0FBQ0YsSUFBSSx1QkFBdUIsSUFBSSxpQkFBaUIsRUFBRSxDQUFDO0lBQ2pELHVCQUF1QixDQUFDLGdCQUFnQixDQUFDLE9BQU8sRUFBRTtRQUNoRCxJQUFNLEdBQUcsR0FBRyxJQUFJLEdBQUcsQ0FBQyxNQUFNLENBQUMsUUFBUSxDQUFDLElBQUksQ0FBQyxDQUFDO1FBQzFDLEdBQUcsQ0FBQyxZQUFZLENBQUMsR0FBRyxDQUFDLEdBQUcsRUFBRSxpQkFBaUIsQ0FBQyxLQUFLLENBQUMsQ0FBQztRQUNuRCxNQUFNLENBQUMsUUFBUSxDQUFDLElBQUksR0FBRyxVQUFHLEdBQUcsQ0FBQyxJQUFJLENBQUUsQ0FBQztJQUN2QyxDQUFDLENBQUMsQ0FBQztBQUNMLENBQUMiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9rcmFmdGphci8uL3NyYy9yZWdpb24udHMiXSwic291cmNlc0NvbnRlbnQiOlsiLy8gc2VhcmNoIGZsb3dcbmNvbnN0IHNlYXJjaFJlZ2lvbklucHV0OiBIVE1MSW5wdXRFbGVtZW50ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihcbiAgJyN0YWJsZS1zZWFyY2gtcmVnaW9ucycsXG4pO1xuY29uc3Qgc2VhcmNoUmVnaW9uSW5wdXRCdXR0b24gPSBkb2N1bWVudC5xdWVyeVNlbGVjdG9yKFxuICAnI3RhYmxlLXNlYXJjaC1yZWdpb24tYnV0dG9uJyxcbik7XG5pZiAoc2VhcmNoUmVnaW9uSW5wdXRCdXR0b24gJiYgc2VhcmNoUmVnaW9uSW5wdXQpIHtcbiAgc2VhcmNoUmVnaW9uSW5wdXRCdXR0b24uYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCAoKSA9PiB7XG4gICAgY29uc3QgdXJsID0gbmV3IFVSTCh3aW5kb3cubG9jYXRpb24uaHJlZik7XG4gICAgdXJsLnNlYXJjaFBhcmFtcy5zZXQoJ3EnLCBzZWFyY2hSZWdpb25JbnB1dC52YWx1ZSk7XG4gICAgd2luZG93LmxvY2F0aW9uLmhyZWYgPSBgJHt1cmwuaHJlZn1gO1xuICB9KTtcbn1cbiJdLCJuYW1lcyI6W10sInNvdXJjZVJvb3QiOiIifQ==