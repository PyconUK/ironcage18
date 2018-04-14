(function($) {
  $('#id_requested_ticket_only').change(maybeShowRestOfForm);

  function maybeShowRestOfForm() {
    var requestedTicketOnly = $('#id_requested_ticket_only')[0].value;

    $('#further-assistance').hide();

    if (requestedTicketOnly == "False") {
      $('#further-assistance').show();
    }
  }

  maybeShowRestOfForm();
})(jQuery);
