/* 
 * Utility functions
 * Remove duplication in code
 */

let modalShown = false;

function configPostModals() {
    // Configures the modals "attached" to a post

    let form_ids = [
        "edit-post-form",
        "delete-post-form",
        "share-post-form",
        "copy-link-form"
    ]

    // Clear interval when modal shows up and reset interval
    // when modal disappears
    for (let id of form_ids) {

        $('[id=' + id + ']').each(function () {
            let modal = $(this).find('.modal');

            // Clear interval when modal is open
            $(modal).on('show.bs.modal', function () {
                let modal_id = $(modal).attr('id');
                
                modalShown = true;  // modal opened by user

                clearInterval(interval);

                if (id === "edit-post-form")
                    toggle("#" + modal_id);
            });
    
            // Reset interval when modal is hidden
            $(modal).on('hidden.bs.modal', function () {
                interval = setInterval(update, intervalInMs);

                modalShown = false;
            });
        });

    }

};