// (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
//
// ALL RIGHTS RESERVED


$(document).ready(function() {
    prepare_login()
})

function listerController($scope) {
    $scope.items = [
        { name: "alpha", id: 1, edit_linkage: '1234',  delete_linkage: '12345' },
        { name: "beta",  id: 2, edit_linkage: '12346', delete_linkage: '12347' }
    ];
}

function api_call(url, method, on_success) {
    username = localStorage.getItem('loginUser')
    password = localStorage.getItem('loginPassword')
    up = username + ":" + password
    up = Base64.encode(up)

    $.ajax({
        url : url,
        crossDomain: true,
        async: false,
        dataType : 'json',
        type: method,
        beforeSend : function(xhr) {
            xhr.setRequestHeader("Authorization", "Basic " + up);
            return true
        },
        error : function(xhr, ajaxOptions, thrownError) {
            alert("failed")
        },
        success : function(data, status, xhr) {
            on_success(data)
        }
    });
}

function login_setup() {
    loginUser = localStorage.getItem("loginUser");
    if ((loginUser == '') || (loginUser == null)) {
        loginUser = 'admin'
    }
    $('#loginUser').val(loginUser)
}

function login_submit() {
    loginUser     = $('#loginUser').val()
    loginPassword = $('#loginPassword').val()
    localStorage.setItem("loginUser", loginUser)
    localStorage.setItem("loginPassword", loginPassword)

    // TODO: test API hit and dismiss only if successful
    api_call('/api/', 'GET', function(data) {
        // alert(data)
        $('#loginModal').modal('hide')
        set_nav_callbacks()
    })
}

function login_clear() {
     localStorage.setItem('loginUser','')
     localStorage.setItem('loginPassword', '')
     $('#loginUser').val('')
     $('#loginPassword').val('')
}

function set_on_enter(id, cb) {
    $(id).keypress(function(event) {
        if ( event.which == 13 ) {
            event.preventDefault();
            cb()
        }
    })
}

function set_nav_callbacks() {

    $('#groupsNav').click(function() {
        load_groups();
    })
    $('#usersNav').click(function() {
        load_users();
    })
    $('#hostsNav').click(function() {
        load_hosts();
    })
    $('#logoutNav').click(function() {
        logout();
    })
    load_users();
}

function load_groups() {
    $('#whatMode').text('Groups')
    window.app_context = 'groups'
}

function load_users() {
    $('#whatMode').text('Users')
    window.app_context = 'users'
}

function load_hosts() {
    $('#whatMode').text('Hosts')
    window.app_context = 'hosts'
}

function logout() {
    login_clear();
    $("#loginModal").modal(keyboard=false);
}

function click_edit_id(id) {
    // TODO: spawn the appropriate view_or_edit modal, don't actually edit in this function
    alert("imagine editing a " + window.app_context + " with ID " + id)
}

function click_delete_id(id) {
    // TODO: spawn the delete confirmation modal, don't actually edit in this function
    alert("imagine deleting a " + window.app_context + " with ID " + id)
}

function prepare_login() {
    $("#loginModal").modal(keyboard=false)
    login_setup()
    set_on_enter("#loginUser", login_submit)
    set_on_enter("#loginPassword", login_submit)
    $("#loginSubmit").click(login_submit)
    $("#loginClear").click(login_clear)
}


