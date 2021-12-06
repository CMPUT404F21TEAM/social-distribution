/*
* Clears post form on closing modal
* Handles showing posts and github activity
* If posts are shown, github activity is hidden and vice versa
* 
* Makes GET request to location.href and displays any
* changes to home posts and github activity without
* refreshing the page
* 
*/

const intervalInMs = 5000;
let interval = setInterval(update, intervalInMs);     // update every 5 seconds

function showPostsOnly () {
    $('label#posts-radio').addClass('active')
    $('label#github-radio').removeClass('active')
    $('#regular-posts').css('display', 'inline');
    $('#github-activity').css('display', 'none');
}

function showGithubOnly () {
    $('label#posts-radio').removeClass('active')
    $('label#github-radio').addClass('active')
    $('#regular-posts').css('display', 'none');
    $('#github-activity').css('display', 'inline');
}

// Make a GET request to updte posts and github acitivity
function update() {
    console.log("Update");
    
    $.ajax({
        url: location.href,
        type: "GET",
        success: function (data) {
            console.log('Success');
            
            if (!modalShown) {
                let new_github = $(data).find('#github-activity').html();
                let new_posts = $(data).find('#regular-posts').html();
    
                // Update github activity
                $('#github-activity').html(new_github);
    
                // Update posts
                $('#regular-posts').html(new_posts);
    
                configPostModals();
                handleMarkDown();
            }
        },
        error: function (data) {
            console.log("Error");
        }
    })
}

$('#posts-radio').on('change', showPostsOnly)
$('#github-radio').on('change', showGithubOnly)

$('#add_post_modal').on('show.bs.modal', function () {
    modalShown = true;
    clearInterval(interval);
    toggle('#add_post_modal');
});

$('#add_post_modal').on('hidden.bs.modal', function () {
    modalShown = false;
    $('#create_post_form').trigger('reset');
    interval = setInterval(update, intervalInMs);     // update every 30 seconds
})

if ($('input[name="feed-type"]:checked').val() == "1") {
    showPostsOnly();
}
else {
    showGithubOnly();
}

configPostModals();