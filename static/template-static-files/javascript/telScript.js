$(document).ready(function () {

  $('#phoneMsg').text('');
  

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
        $('#phoneMsg').text('');
        $('#phoneMsg').text('Valid');
        $("#phoneMsg").css("color", "green");

        phoneFinalVar = iti.getNumber();
        phoneCode = iti.getSelectedCountryData();
        document.getElementById("btn-submit").disabled = false;

      }
      else {
        var errorCode = iti.getValidationError();
        $('#phoneMsg').text('');
        $('#phoneMsg').text(errorMap[errorCode]);
        document.getElementById("btn-submit").disabled = true;    
      }
    }

  });


  $('#btn-submit').on('click', function () { 
      $("#id_phone_number").val(phoneFinalVar);
  });
  
  
});

