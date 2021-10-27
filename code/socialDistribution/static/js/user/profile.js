    // Enable Edit form 
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
            $('#email').focus()
        }
    })

    $('input').on('input', () => {
        // show submit button
        $('#profile_submit_button').removeClass('d-none');
    })