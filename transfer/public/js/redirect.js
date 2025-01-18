console.log("redirected");
if (window.location.pathname === '/app/alalmia') {
    window.location.href = "/app/alalmiatransfer";
}
else
if (window.location.pathname === "/app/home") {
    window.location.href = "/app/alalmiatransfer";
}
else
if (window.location.pathname === "/app") {
    window.location.href = "/app/alalmiatransfer";
}