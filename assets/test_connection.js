$('#test-connection').click(function(){
    var url = $('#url').val();
    var passcode = $('#passcode').val();
    var nonce = init.csrfNonce;

    $.post("/test-connection",
    {
        url:url,
        passcode:passcode,
        nonce:nonce
    },
    function(data,status){
        $('#test-connection').removeClass('btn-info');
        if(data == 'Success'){
            $('#test-connection').addClass('btn-success');
            $('#test-connection').text('Success');
        }
        else{
            $('#test-connection').addClass('btn-danger');
            $('#test-connection').text('Error');
        }
        setTimeout(function(){
            //无脑全删掉
            $('#test-connection').removeClass('btn-success');
            $('#test-connection').removeClass('btn-danger');
            $('#test-connection').addClass('btn-info');
            $('#test-connection').text('Test Connection');
        }, 3000);
    });
})