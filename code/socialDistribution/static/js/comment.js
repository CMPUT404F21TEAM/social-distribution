    /**
     * Redirect to home page of local author
     * */
     function redirectToAuhtorPage(author_type, id) {
        if (author_type === "Local") {
            location.href = `${location.protocol}//${location.host}/app/author/${id}`;
        }
    }