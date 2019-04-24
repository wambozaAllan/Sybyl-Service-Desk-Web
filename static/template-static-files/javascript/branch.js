$(document).ready(function () {

  $('validMsg').text('');

  $("#id_phone_number").keypress(function(event) {
    return /\d/.test(String.fromCharCode(event.keyCode));
  });


  $("#id_location").keypress(function(event) {
    return /\D/.test(String.fromCharCode(event.keyCode));
  });

  $("#id_name").keypress(function(event) {
    return /\D/.test(String.fromCharCode(event.keyCode));
  });


  var phoneFinalVar;
  var input = document.querySelector("#id_phone_number");
  var emailInput = document.querySelector("#id_email_address");

  var iti = window.intlTelInput(input, {
    autoPlaceholder: "polite",
    separateDialCode: true,
    initialCountry: 'UG',
    placeholderNumberType: 'MOBILE',
    preferredCountries: ["ug", 'ke', 'tz', 'rw'],
    utilsScript: "utils.js",

  });



  var errorMap = ["Invalid number", "Invalid country code", "Too short", "Too long"];

  $("#id_phone_number").on('input', function(){
    if (input.value.trim()) {
      if (iti.isValidNumber()) {
        $('#validMsg').text('');
        $('#validMsg').text('Valid');
        $('#validMsg').css("color", "green");

        phoneFinalVar = iti.getNumber();
        document.getElementById("btn-submit").disabled = false;

      }
      else {
        var errorCode = iti.getValidationError();
        $('#validMsg').text('');
        $('#validMsg').text(errorMap[errorCode]);
        $('#validMsg').css("color", "red");

        document.getElementById("btn-submit").disabled = true;
      }
    }

  });

  function emailIsValid (email) {
      return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
  }

  function IsEmail(email) {
      var regex = /^([a-zA-Z0-9_\.\-\+])+\@(([a-zA-Z0-9\-])+\.)+([a-zA-Z0-9]{2,4})+$/;
      if(!regex.test(email)) {
        return false;
      }else{
        return true;
      }
}

    function EmailValidate() {
     var numericExpression = /^w.+@[a-zA-Z_-]+?.[a-zA-Z]{2,3}$/;
     var elem = $("#id_email_address").val();
     if (elem.match(numericExpression))
     return true;
     else
     return false;
     }



   $('#id_email_address').on('change', function(){

        if(IsEmail(emailInput) === false){
//           $('#id_email_address').val("false");
            console.log("fdsadfsdf")
        }
        else{
            console.log("truee")
        }

   })

  $('#btn-submit').on('click', function () {
        $("#id_phone_number").val(phoneFinalVar);
//        if (!IsEmail()) {
//            alert("Email validaiton failed");
//            console.log("fail")
//        }
//        else{
//            alert("Email passed")
//        }
  });





});

