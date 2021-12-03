// Makes GET request to location.href and displays any
// changes to home posts and github activity without
// refreshing the page

function update() {
    console.log("Update");
    
    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');
            let new_github = $(data).find('#github-activity').html();
            let new_posts = $(data).find('#regular-posts').html();

            // Update github activity
            $('#github-activity').html(new_github);

            // Update posts
            $('#regular-posts').html(new_posts);
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

setInterval(update, 30000);     // update every 30 seconds