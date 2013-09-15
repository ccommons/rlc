var __CKEDITOR_CONFIGS = {
    default : {
    },
    doceditor : {
        allowedContent: true,
        height: '500px'
    },
    annotation_compose : {
        toolbar: [ [ 'Source', '-', 'Bold', 'Italic' ]]
    }
}

function verify_json_response(data) {
    if (data.hasOwnProperty("error")) {
        if (data["error"] === 'logged_out') {
            if (data.hasOwnProperty("login_url")) {
                window.location.replace(data["login_url"]);
            } else {
                // this case is usually preferable; the mandatory login
                // redirector will help return to previous context
                location.reload();
            }
        }
    }
}
