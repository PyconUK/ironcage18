$(document).ready(function() {
    if (typeof csrfToken !== 'undefined') {
        $.ajaxSetup({
            beforeSend: function (xhr, settings) {
                if (!this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrfToken);
                }
            }
        });

        $('.selectable-schedule').click(function (e) {
            var proposalId = e.currentTarget.dataset.proposal;
            var method = 'POST';

            if ($(e.currentTarget).hasClass('selected')) {
                method = 'DELETE';
            }

            $.ajax({
                url: '/schedule/interest/?id=' + proposalId,
                type: method,
                success: function (result) {
                    $(e.currentTarget).toggleClass('selected');
                }
            });
        })
    }
})
