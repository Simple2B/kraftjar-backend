/******/ (() => { // webpackBootstrap
/*!************************!*\
  !*** ./src/service.ts ***!
  \************************/
// search flow
var searchServiceInput = document.querySelector('#table-search-services');
var searchServiceInputButton = document.querySelector('#table-search-service-button');
if (searchServiceInputButton && searchServiceInput) {
    searchServiceInputButton.addEventListener('click', function () {
        var url = new URL(window.location.href);
        url.searchParams.set('q', searchServiceInput.value);
        window.location.href = "".concat(url.href);
    });
}

/******/ })()
;
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoianMvc2VydmljZS5qcyIsIm1hcHBpbmdzIjoiOzs7O0FBQUEsY0FBYztBQUNkLElBQU0sa0JBQWtCLEdBQXFCLFFBQVEsQ0FBQyxhQUFhLENBQ2pFLHdCQUF3QixDQUN6QixDQUFDO0FBQ0YsSUFBTSx3QkFBd0IsR0FBRyxRQUFRLENBQUMsYUFBYSxDQUNyRCw4QkFBOEIsQ0FDL0IsQ0FBQztBQUNGLElBQUksd0JBQXdCLElBQUksa0JBQWtCLEVBQUUsQ0FBQztJQUNuRCx3QkFBd0IsQ0FBQyxnQkFBZ0IsQ0FBQyxPQUFPLEVBQUU7UUFDakQsSUFBTSxHQUFHLEdBQUcsSUFBSSxHQUFHLENBQUMsTUFBTSxDQUFDLFFBQVEsQ0FBQyxJQUFJLENBQUMsQ0FBQztRQUMxQyxHQUFHLENBQUMsWUFBWSxDQUFDLEdBQUcsQ0FBQyxHQUFHLEVBQUUsa0JBQWtCLENBQUMsS0FBSyxDQUFDLENBQUM7UUFDcEQsTUFBTSxDQUFDLFFBQVEsQ0FBQyxJQUFJLEdBQUcsVUFBRyxHQUFHLENBQUMsSUFBSSxDQUFFLENBQUM7SUFDdkMsQ0FBQyxDQUFDLENBQUM7QUFDTCxDQUFDIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8va3JhZnRqYXIvLi9zcmMvc2VydmljZS50cyJdLCJzb3VyY2VzQ29udGVudCI6WyIvLyBzZWFyY2ggZmxvd1xuY29uc3Qgc2VhcmNoU2VydmljZUlucHV0OiBIVE1MSW5wdXRFbGVtZW50ID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihcbiAgJyN0YWJsZS1zZWFyY2gtc2VydmljZXMnLFxuKTtcbmNvbnN0IHNlYXJjaFNlcnZpY2VJbnB1dEJ1dHRvbiA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoXG4gICcjdGFibGUtc2VhcmNoLXNlcnZpY2UtYnV0dG9uJyxcbik7XG5pZiAoc2VhcmNoU2VydmljZUlucHV0QnV0dG9uICYmIHNlYXJjaFNlcnZpY2VJbnB1dCkge1xuICBzZWFyY2hTZXJ2aWNlSW5wdXRCdXR0b24uYWRkRXZlbnRMaXN0ZW5lcignY2xpY2snLCAoKSA9PiB7XG4gICAgY29uc3QgdXJsID0gbmV3IFVSTCh3aW5kb3cubG9jYXRpb24uaHJlZik7XG4gICAgdXJsLnNlYXJjaFBhcmFtcy5zZXQoJ3EnLCBzZWFyY2hTZXJ2aWNlSW5wdXQudmFsdWUpO1xuICAgIHdpbmRvdy5sb2NhdGlvbi5ocmVmID0gYCR7dXJsLmhyZWZ9YDtcbiAgfSk7XG59XG4iXSwibmFtZXMiOltdLCJzb3VyY2VSb290IjoiIn0=