/*
 * Handles showing posts and github activity
 * If posts are shown, github activity is hidden and vice versa
 */

function show(item) {
    $(item['label_id']).addClass('active');
    $(item['item_id']).css('display', 'inline');
}

function hide(item) {
    $(item['label_id']).removeClass('active');
    $(item['item_id']).css('display', 'none');
}

inbox_posts_ids = {
    'label_id': 'label#inbox-posts-radio',
    'input_id': '#inbox-posts-radio',
    'item_id': '#inbox-posts'
}

follow_reqs_ids = {
    'label_id': 'label#follow-radio',
    'input_id': '#follow-radio',
    'item_id': '#follow-requests'
}

github_ids = {
    'label_id': 'label#github-radio',
    'input_id': '#github-radio',
    'item_id': '#github-activity'
}

$(inbox_posts_ids['input_id']).on('change', function () {
    show(inbox_posts_ids);
    hide(follow_reqs_ids);
    hide(github_ids);
})

$(github_ids['input_id']).on('change', function () {
    show(github_ids);
    hide(inbox_posts_ids);
    hide(follow_reqs_ids);
})

$(follow_reqs_ids['input_id']).on('change', function () {
    show(follow_reqs_ids);
    hide(inbox_posts_ids);
    hide(github_ids);
})


if ($('input[name="feed-type"]:checked').val() == "1") {
    show(inbox_posts_ids);
    hide(follow_reqs_ids);
    hide(github_ids);
}
else if ($('input[name="feed-type"]:checked').val() == "2") {
    show(follow_reqs_ids);
    hide(inbox_posts_ids);
    hide(github_ids);
}
else {
    show(github_ids);
    hide(inbox_posts_ids);
    hide(follow_reqs_ids);
}