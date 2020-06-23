var challenge_id = $('#challenge-id').attr('value');
var nonce = init.csrfNonce;

var timer;
var timeout = 3600;

$(document).ready(function () {
    $.get('/status?challenge_id=' + challenge_id,
        function (data, status) {
            datas = data.split(' ');
            if (datas[0] == 'Success') {
                con_url = datas[1];
                new_timeout = datas[2];
                doDeploy(new_timeout, con_url);
            } else if (data == 'No') {
                return;
            } else {
                alert('Error');
            }
        });
})

$('#dynamic_deploy').on('click', '#deploy', function () {
    $.post('/deploy', {
            challenge_id: challenge_id,
            nonce: nonce
        },
        function (data, status) {
            datas = data.split(' ');
            if (datas[0] == 'Success') {
                con_url = datas[1];
                new_timeout = datas[2];
                doDeploy(new_timeout, con_url);
            } else if (data == 'Repeat') {
                alert('One user can only deploy one container!')
            } else {
                alert('Error');
            }
        });
});

$('#dynamic_deploy').on('click', '#destroy', function () {
    $.post('/destroy', {
            challenge_id: challenge_id,
            nonce: nonce
        },
        function (data, status) {
            if (data == 'Success') {
                doDestroy();
            } else {
                alert('Error');
            }
        });
});

$('#dynamic_deploy').on('click', '#renew', function () {
    $.post('/renew', {
            challenge_id: challenge_id,
            nonce: nonce
        },
        function (data, status) {
            if (data == 'Success') {
                timeout = 3600
            } else {
                alert('Error');
            }
        });
});

function doDeploy(new_timeout, con_url) {
    var destroy_btn = '<button class="btn btn-danger" id="destroy" style="width: 40%;margin-left: 5%;">Destroy</button>';
    var renew_btn = '<button class="btn btn-primary" id="renew" style="width: 40%;margin-right: 5%;float:right">Renew</button>';
    var parent_div = $("#deploy").parent();
    var timeout_h = '<h6 class="form-text text-muted" id="timeout"></h6>';
    var con_url_h = '<h6 class="form-text" id="con_url">' + con_url + '</h6>';
    timeout = new_timeout

    parent_div.empty();
    parent_div.append(timeout_h)
    parent_div.append(con_url_h)
    parent_div.append(destroy_btn);
    parent_div.append(renew_btn);

    timer = clearInterval(timer);
    timer = null

    timer = window.setInterval(function () {
        if (timeout > 0) {
            $('#timeout').html('Remaining Time: ' + timeout + 's');
            timeout--;
        } else {
            doDestroy();
        }
    }, 1000);
}

function doDestroy() {
    var deploy_btn = '<button class="btn btn-success" id="deploy" style="width: 40%;">Deploy</button>';
    var parent_div = $("#destroy").parent();

    parent_div.empty();
    parent_div.append(deploy_btn);
    timer = clearInterval(timer);
    timer = null
}