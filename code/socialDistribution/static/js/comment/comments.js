$('#newCommentTextArea').on('input propertychange', function () {
    // enable button if comment not empty
    if (this.value.length) {
        $('#newCommentButton').prop('disabled', false);
    } else {
        $('#newCommentButton').prop('disabled', true);
    }
})