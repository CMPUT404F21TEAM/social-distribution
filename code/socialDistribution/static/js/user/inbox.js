/*
 * Makes GET request to location.href and applies
 * updates to the inbox without refreshing the page
 * 
 */

let intervalInMs = 5000;
let interval = setInterval(update, intervalInMs);     // update every 5 seconds

function update() {
    console.log("Update");
    
    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');

            if (!modalShown) {
                let inbox = $(data).find('.inbox').html();
                $('.inbox').html(inbox);
    
                configPostModals()
                handleMarkDown();
            }
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

configPostModals();