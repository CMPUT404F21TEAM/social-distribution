/* 
 * Makes a GET request to the location.href and replaces the
 * posts of the author in the author-prof-posts div by
 * the new ones in the returned data
 * Enable Edit form
 * 
 */

const intervalInMs = 5000;
let interval = setInterval(update, intervalInMs)    // fetch every 5 seconds

function update() {
    console.log("Update");

    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');
            let new_posts = $(data).find('.author-prof-posts').html();

            // Update posts
            $('.author-prof-posts').html(new_posts);

            configPostModals();
            handleMarkDown();
        },
        error: function (data) {
            console.log("Error");
        }
    })
}


configPostModals();