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
            let new_requests = $(data).find('.follow-requests');
            let new_posts = $(data).find('.inbox-posts');

            let empty_inbox = $(data).find('.empty-inbox');
            let current_empty_inbox = $(document).find('.empty-inbox');

            if (empty_inbox.length === 0 && current_empty_inbox.length !== 0)
                current_empty_inbox.remove();

            // Update follow requests
            $('.follow-requests').html(new_requests.html());

            // Update posts
            $('.inbox-posts').html(new_posts.html());

            configEditPostModal()
            handleMarkDown();
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

configEditPostModal();