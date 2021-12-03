// Makes GET request to location.href and applies
// updates to the inbox without refreshing the page

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
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

setInterval(update, 30000);     // update every 30 seconds