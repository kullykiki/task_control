$(document).ready(function () {
    // Function to navigate form steps
    function navigateFormStep(direction, currentStep) {
        var nextStep = direction === 'next' ? currentStep + 1 : currentStep - 1;
        $('#step-' + currentStep).addClass('d-none');
        $('#step-' + nextStep).removeClass('d-none');
    }

    $('.btn-navigate-form-step').click(function () {
        var direction = $(this).attr('data-direction');
        var currentStep = parseInt($(this).attr('data-step'));
        navigateFormStep(direction, currentStep);
        // Stop the default behavior of the link
        return false;
    });
    
});
