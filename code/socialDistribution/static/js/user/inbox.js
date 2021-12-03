/*
 * Makes GET request to location.href and applies
 * updates to the inbox without refreshing the page
 * 
 */

let intervalInMs = 3000;
let interval = setInterval(update, intervalInMs);     // update every 30 seconds

function update() {
    console.log("Update");
    
    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');
            let new_requests = $(data).find('.follow-requests').html();
            let new_posts = $(data).find('.inbox-posts').html();

            // Update follow requests
            $('.follow-requests').html(new_requests);

            // Update posts
            $('.inbox-posts').html(new_posts);

            configEditPostModal()
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

configEditPostModal();