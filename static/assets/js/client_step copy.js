document.addEventListener("DOMContentLoaded", () => {
    /**
        * Navigate to the specified step in the form.
        * @param {number} stepNumber - The target step number.
        */
    const navigateToFormStep = (stepNumber) => {
        // Hide all form steps
        document.querySelectorAll(".form-step").forEach((formStepElement) => {
            formStepElement.classList.add("d-none");
        });

        // Mark all form steps as unfinished
        document.querySelectorAll(".form-stepper-list").forEach((formStepHeader) => {
            formStepHeader.classList.add("form-stepper-unfinished");
            formStepHeader.classList.remove("form-stepper-active", "form-stepper-completed");
            const icon = formStepHeader.querySelector(".form-stepper-circle i");
            if (icon) {
                icon.className = "fa-regular fa-circle fa-lg";
            }
        });

        // Show the current form step
        document.querySelector("#step-" + stepNumber).classList.remove("d-none");

        // Mark the current form step as active
        const formStepCircle = document.querySelector('li[step="' + stepNumber + '"]');
        formStepCircle.classList.remove("form-stepper-unfinished", "form-stepper-completed");
        formStepCircle.classList.add("form-stepper-active");
        const activeIcon = formStepCircle.querySelector(".form-stepper-circle i");
        if (activeIcon) {
            activeIcon.className = "fa-solid fa-circle-check fa-lg";
        }

        // Mark all previous steps as completed
        for (let index = 1; index < stepNumber; index++) {
            const formStepCircle = document.querySelector('li[step="' + index + '"]');
            if (formStepCircle) {
                formStepCircle.classList.remove("form-stepper-unfinished", "form-stepper-active");
                formStepCircle.classList.add("form-stepper-completed");
                const completedIcon = formStepCircle.querySelector(".form-stepper-circle i");
                if (completedIcon) {
                    completedIcon.className = "fa-solid fa-circle-check fa-lg";
                }
            }
        }
    };

    // Add click event listener to navigation buttons
    document.querySelectorAll(".btn-navigate-form-step").forEach((formNavigationBtn) => {
        formNavigationBtn.addEventListener("click", () => {
            const stepNumber = parseInt(formNavigationBtn.getAttribute("step_number"));
            navigateToFormStep(stepNumber);
        });
    });
});