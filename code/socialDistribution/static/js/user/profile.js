/* 
 * Makes a GET request to the location.href and replaces the
 * posts of the author in the author-prof-posts div by
 * the new ones in the returned data
 * Enable Edit form
 * 
 */

$( "#profile_edit_button" ).click( event => {
    event.preventDefault(); // don't submit form

    // Loop all inputs
    for (input of $("input")) {
        // prevent username edit
        if (input.name === 'username') {
            continue;
        }

        // enable input
        input.disabled = false;
    }

    // set focus and cursor to first editable input end
    firstNameInput = $('#first_name')
    firstNameInputValue = firstNameInput.focus().val();
    firstNameInput.val('').val(firstNameInputValue);
})

$('input').on('input', () => {
    // show submit button
    $('#profile_submit_button').removeClass('d-none');
})


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

            configEditPostModal();
            handleMarkDown();
        },
        error: function (data) {
            console.log("Error");
        }
    })
}


configEditPostModal();