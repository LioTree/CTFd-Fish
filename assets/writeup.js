$(document).ready(function () {
    $("#submit-files").click(function () {
        var $input = $('#upload-writeup');
        var files = $input.prop('files');
        var challenge_id = $('#challenge-id').attr('value');
        var challenge_name = $('.challenge-name').text();
        var data = new FormData();
        data.append('writeup', files[0]);
        data.append('challenge_id', challenge_id)
        data.append('challenge_name', challenge_name)
        data.append('nonce', init.csrfNonce);

        $.ajax({
            url: '/writeup',
            type: 'POST',
            data: data,
            cache: false,
            processData: false,
            contentType: false,
            success: function (result) {
                if (result == 'Success')
                    uploaded_message();
                else
                    error_message();
            },
            error: function(xhr,status,error){
                error_message();
            }
        });
    });

    $("#writeup-tab").click(function () {
        var challenge_id = $('#challenge-id').attr('value');
        url = '/writeup?cid=' + challenge_id;
        $.get(url, function (data, status) {
            if (data == 'Uploaded')
                uploaded_message();
        });
    });

    var uploaded_message = function () {
        $("#upload-result-message").text('Uploaded');
        $("#upload-result-notification").removeClass('alert-info');
        $("#upload-result-notification").addClass('alert-success');
    };

    var error_message = function () {
        var pre_text = $("#upload-result-message").text();
        $("#upload-result-message").text('Error');
        $("#upload-result-notification").addClass('alert-danger');
        setTimeout(function () {
            $("#upload-result-notification").removeClass('alert-danger');
            $("#upload-result-message").text(pre_text);
        }, 3000);
    }
});