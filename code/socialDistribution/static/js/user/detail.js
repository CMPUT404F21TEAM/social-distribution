/* 
 * Makes a GET request to the location.href and replaces the
 * posts of the author in the author-prof-posts div by
 * the new ones in the returned data
 * Enable Edit form
 * 
 */

const intervalInMs = 20000;
let interval = setInterval(update, intervalInMs)    // fetch every 20 seconds

function update() {
    console.log("Update");

    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');
            
            if (!modalShown) {
                let new_posts = $(data).find('.author-prof-posts').html();
                
                // Update posts
                $('.author-prof-posts').html(new_posts);
    
                configPostModals();
                handleMarkDown();
            }
        },
        error: function (data) {
            console.log("Error");
        }
    })
}


configPostModals();