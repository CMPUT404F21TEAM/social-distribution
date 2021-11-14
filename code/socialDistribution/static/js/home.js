/*
 * Clears post form on closing modal
 * Handles showing posts and github activity
 * If posts are shown, github activity is hidden and vice versa
 */

$('#add_post_modal').on('hidden.bs.modal', function () {
    $('#create_post_form').trigger('reset');
})

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

$('#posts-radio').on('change', showPostsOnly)
$('#github-radio').on('change', showGithubOnly)

if ($('input[name="feed-type"]:checked').val() == "1") {
    showPostsOnly();
}
else {
    showGithubOnly();
}