$(document).ready(function() {
    if (typeof csrfToken !== 'undefined') {
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });

        $('.selectable-interest').click(function (e) {
            var proposalId = e.currentTarget.dataset.proposal;
            var method = 'POST';

            if ($(".selectable-schedule[data-proposal='" + proposalId + "']").hasClass('selected')) {
                method = 'DELETE';
            }

            $.ajax({
                url: '/schedule/interest/?id=' + proposalId,
                type: method,
                success: function (result) {
                    $(".selectable-schedule[data-proposal='" + proposalId + "']").toggleClass('selected');
                    $(e.currentTarget).toggleClass('fa-calendar-minus-o')
                    $(e.currentTarget).toggleClass('fa-calendar-plus-o')
                }
            });
        })
    }
})
