/*
 * Clears post form on closing modal
 */

$('#add_post_modal').on('hidden.bs.modal', function () {
    $('#create_post_form').trigger('reset');
})