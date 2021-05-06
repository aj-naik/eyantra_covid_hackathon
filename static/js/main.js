$(".otp-input").hide();

$("#mobile-button").click(function(){
    $(".mobile-input").hide();
    $(".otp-input").show();
});
$("#otp-button").click(function(){
    $("#check").show();
    $(".otp-input").hide();
    
})