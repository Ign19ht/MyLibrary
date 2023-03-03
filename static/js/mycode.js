var login = document.getElementById("loginButton");
var username_filed = document.getElementById("usernameField");
var password_filed = document.getElementById("passwordField");
var message = document.getElementById("message")

login.addEventListener("click", evt => {
    evt.preventDefault();
    if (username_filed.value.length == 0 || password_filed.value.length == 0) {
        message.textContent = "Both fields must be filled"
        return 0;
    }
    let xhr = new XMLHttpRequest();
    xhr.open('POST', '/auth', true);
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    var body = 'username=' + encodeURIComponent(username_filed.value) +
        '&password=' + encodeURIComponent(password_filed.value);
    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            let response = xhr.response;
            if (response === '"wrong username or password"') {
                message.textContent = "Wrong password"
            } else if (response === '"accepted"') {
                window.open("/","_self")
                alert("authentication complete")
            }
        }
    }
    xhr.send(body);
})



