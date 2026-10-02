document.addEventListener("htmx:beforeSwap", function (event) {
    var xhr = event.detail.xhr;
    var contentType = xhr ? xhr.getResponseHeader("Content-Type") : null;
    if (xhr && xhr.status >= 400 && contentType && contentType.startsWith("text/html")) {
        event.detail.shouldSwap = true;
        event.detail.isError = false;
    }
});
