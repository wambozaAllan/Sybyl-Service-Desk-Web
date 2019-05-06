/*document.querySelector('.sweet-wrong').onclick = function(){
    sweetAlert("Oops...", "Something went wrong !!", "error");
};
document.querySelector('.sweet-message').onclick = function(){
    swal("Hey, Here's a message !!")
};
document.querySelector('.sweet-text').onclick = function(){
    swal("Hey, Here's a message !!", "It's pretty, isn't it?")
};
document.querySelector('.sweet-success').onclick = function(){
    swal("Hey, Good job !!", "You clicked the button !!", "success")
};
document.querySelector('.sweet-confirm').onclick = function(){
    swal({
            title: "Are you sure to delete ?",
            text: "You will not be able to recover this imaginary file !!",
            type: "warning",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Yes, delete it !!",
            closeOnConfirm: false
        },
        function(){
            swal("Deleted !!", "Hey, your imaginary file has been deleted !!", "success");
        });
};*/

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function validateEmail(email) {
  var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
  return re.test(email);
}

function validate(email) {
   var csrftoken = getCookie('csrftoken');
  if (validateEmail(email)) {
    $.ajax({
            url: "/core/password-reset/",
            type: "POST",
            data: {
                email: email
            },
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            },
            success: function () {
                swal("Nice!", "A password reset link has been sent to: " + email, "success");
                },
            error: function (xhr, ajaxOptions, thrownError) {
                swal("Error!", "Error generating password reset link. Please try again", "error");
            }
        });
  } else {
   swal.showInputError("Hey, "+ email +" is not a valid email!");
   return false
  }
}

document.querySelector('.forgot-password').onclick = function(){
    swal({
            title: "Enter your Email",
            text: "A new password will be generated and sent to your email address !!",
            type: "input",
            showCancelButton: true,
            confirmButtonColor: "#DD6B55",
            confirmButtonText: "Yes, send !!",
            cancelButtonText: "No, cancel it !!",
            closeOnConfirm: false,
            closeOnCancel: false
        },
        function(inputValue){
            if (inputValue === false){
              swal("Oooops!", "Process cancelled", "error");
              return false;
            }

            if (inputValue === "") {
              swal.showInputError("Hey, you need to type in your email!");
              return false
            }

            if(inputValue !== "") {
             validate(inputValue);
            }
        });
};

/*document.querySelector('.sweet-image-message').onclick = function(){
    swal({
        title: "Sweet !!",
        text: "Hey, Here's a custom image !!",
        imageUrl: "images/hand.jpg"
    });
};
document.querySelector('.sweet-html').onclick = function(){
    swal({
        title: "Sweet !!",
        text: "<span style='color:#ff0000'>Hey, you are using HTML !!<span>",
        html: true
    });
};
document.querySelector('.sweet-auto').onclick = function(){
    swal({
        title: "Sweet auto close alert !!",
        text: "Hey, i will close in 2 seconds !!",
        timer: 2000,
        showConfirmButton: false
    });
};
document.querySelector('.sweet-prompt').onclick = function(){
    swal({
            title: "Enter an input !!",
            text: "Write something interesting !!",
            type: "input",
            showCancelButton: true,
            closeOnConfirm: false,
            animation: "slide-from-top",
            inputPlaceholder: "Write something"
        },
        function(inputValue){
            if (inputValue === false) return false;
            if (inputValue === "") {
                swal.showInputError("You need to write something!");
                return false
            }
            swal("Hey !!", "You wrote: " + inputValue, "success");
        });
};
document.querySelector('.sweet-ajax').onclick = function(){
    swal({
            title: "Sweet ajax request !!",
            text: "Submit to run ajax request !!",
            type: "info",
            showCancelButton: true,
            closeOnConfirm: false,
            showLoaderOnConfirm: true,
        },
        function(){
            setTimeout(function(){
                swal("Hey, your ajax request finished !!");
            }, 2000);
        });
};
*/
