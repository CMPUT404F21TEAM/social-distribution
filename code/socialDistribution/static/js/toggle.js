/*
 *  Handlers used in the form for creating and editing posts
 *  - Toggles the post recipients
 *    That is, hides and shows the list recipients based on the post visibility
 *  
 *  - Toggles the content type of the post.
 *    That is, changes the input field of the content depending on the chosed 
 *    content type of the post
 */

function toggle(modal_id) {
    // form.post_type expands to an input tag with "id_post_type" as id
    var post_type = document.querySelector(modal_id + ' #id_post_type');
    var content_text_div = document.querySelector(modal_id + ' #content_text_div');
    var image_upload_div = document.querySelector(modal_id + ' #image_upload_div');
    console.log(post_type);
    
    function toggleContentInputHandler(ev) {
        if (this.value == "TEXT") {
            content_text_div.style.display = "block";
            image_upload_div.style.display = "none";
        }
        else {
            image_upload_div.style.display = "block";
            content_text_div.style.display = "none";
        }
    }

    toggleContentInputHandler.call(post_type);
    post_type.addEventListener('change', toggleContentInputHandler.bind(post_type));

    // form.visibility expands to an input tag with "id_visibility" as id
    var visibility_check = document.querySelector(modal_id + ' #id_visibility');
    var post_recipients_div = document.querySelector(modal_id + ' #post_recipients_div');
    function toggleRecipientsHandler (ev) {
        if (this.value == "PR")
            post_recipients_div.style.display = "block";
        else
            post_recipients_div.style.display = "none";
    }

    visibility_check.addEventListener('change', toggleRecipientsHandler.bind(visibility_check));
    toggleRecipientsHandler.call(visibility_check);
}