$(document).ready(function(){
    $(".content-markdown").each(function(){
      var content = $(this).text()
      console.log("content",content)
      var markedContent = marked(content)
      $(this).html(markedContent)
    })
  })
