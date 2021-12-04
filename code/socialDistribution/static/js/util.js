/* 
 * Utility functions
 * Remove duplication
 */

function configEditPostModal() {

    // Clear interval when modal shows up and reset interval
    // when modal disappears

    $('[id=edit-post-form]').each(function () {
        let modal = $(this).find('.modal');
        $(modal).on('show.bs.modal', function () {
            let modal_id = $(modal).attr('id');
            clearInterval(interval);
            toggle("#" + modal_id);
        });

        $(modal).on('hidden.bs.modal', function () {
            interval = setInterval(update, intervalInMs);
        });
    });

};