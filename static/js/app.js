/**
 * App-wide JS: flash auto-dismiss, submit loading states, signup validation, preferences gym_band toggle.
 * Uses data attributes to hook into markup without inline handlers.
 */
(function () {
    'use strict';

    function ready(fn) {
        if (document.readyState !== 'loading') {
            fn();
        } else {
            document.addEventListener('DOMContentLoaded', fn);
        }
    }

    // ---- Flash auto-dismiss ----
    function initFlashDismiss() {
        var containers = document.querySelectorAll('.flash-container[data-auto-dismiss]');
        containers.forEach(function (container) {
            var ms = parseInt(container.getAttribute('data-auto-dismiss'), 10) || 5000;
            setTimeout(function () {
                container.classList.add('flash-dismissed');
            }, ms);
        });
    }

    // ---- Submit loading: disable button and show spinner for forms with data-loading-on-submit ----
    function initSubmitLoading() {
        var forms = document.querySelectorAll('form[data-loading-on-submit]');
        forms.forEach(function (form) {
            form.addEventListener('submit', function () {
                var btn = form.querySelector('button[type="submit"]');
                if (!btn || btn.disabled) return;
                btn.disabled = true;
                var originalHtml = btn.innerHTML;
                btn.innerHTML = '<span class="btn-loading-spinner" aria-hidden="true"></span> Processing…';
                // If form is invalid or fails, button stays stuck – server redirects on success, so this is ok for happy path.
                // On validation error, page reloads and button resets.
            });
        });
    }

    // ---- Signup validation: forms with data-validate-signup ----
    function initSignupValidation() {
        var form = document.querySelector('form[data-validate-signup]');
        if (!form) return;

        var maxDateStr = form.getAttribute('data-max-date') || '';
        var fullNameInput = form.querySelector('#full_name');
        var dobInput = form.querySelector('#date_of_birth');
        var errorClass = 'border-red-500 focus:border-red-500 focus:ring-red-200';
        var normalClass = 'border-slate-300 focus:border-slate-900 focus:ring-slate-200';

        function clearFieldError(input) {
            if (!input) return;
            input.classList.remove('border-red-500', 'focus:border-red-500', 'focus:ring-red-200');
            input.classList.add('border-slate-300', 'focus:border-slate-900', 'focus:ring-slate-200');
            var wrap = input.closest('.space-y-2');
            if (wrap) {
                var hint = wrap.querySelector('.field-error');
                if (hint) hint.remove();
            }
        }

        function showFieldError(input, message) {
            if (!input) return;
            input.classList.remove('border-slate-300', 'focus:border-slate-900', 'focus:ring-slate-200');
            input.classList.add('border-red-500', 'focus:border-red-500', 'focus:ring-red-200');
            var wrap = input.closest('.space-y-2');
            if (wrap) {
                var existing = wrap.querySelector('.field-error');
                if (existing) existing.remove();
                var hint = document.createElement('p');
                hint.className = 'field-error text-xs text-red-600 font-medium';
                hint.setAttribute('role', 'alert');
                hint.textContent = message;
                input.parentNode.insertBefore(hint, input.nextSibling);
            }
        }

        function ageFromDateStr(str) {
            if (!str) return null;
            var d = new Date(str);
            if (isNaN(d.getTime())) return null;
            var today = new Date();
            var age = today.getFullYear() - d.getFullYear();
            var m = today.getMonth() - d.getMonth();
            if (m < 0 || (m === 0 && today.getDate() < d.getDate())) age -= 1;
            return age;
        }

        form.addEventListener('submit', function (e) {
            var errors = [];
            if (fullNameInput) clearFieldError(fullNameInput);
            if (dobInput) clearFieldError(dobInput);

            var name = (fullNameInput && fullNameInput.value) ? fullNameInput.value.trim() : '';
            if (!name) {
                errors.push({ el: fullNameInput, msg: 'Full name is required.' });
            }

            var dobVal = dobInput ? dobInput.value.trim() : '';
            if (!dobVal) {
                errors.push({ el: dobInput, msg: 'Date of birth is required.' });
            } else {
                var age = ageFromDateStr(dobVal);
                if (age !== null) {
                    if (age < 0) {
                        errors.push({ el: dobInput, msg: 'Invalid date of birth.' });
                    } else if (age < 16) {
                        errors.push({ el: dobInput, msg: 'You must be at least 16 years old to sign up.' });
                    }
                } else {
                    errors.push({ el: dobInput, msg: 'Invalid date format.' });
                }
            }

            if (errors.length) {
                e.preventDefault();
                errors.forEach(function (err) {
                    if (err.el) showFieldError(err.el, err.msg);
                });
                var first = errors[0] && errors[0].el;
                if (first) {
                    first.focus();
                    first.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        });
    }

    // ---- Preferences: toggle gym_band required when "Add-ons only" is selected ----
    function initPreferencesGymBand() {
        var form = document.querySelector('form[data-preferences-form]');
        if (!form) return;
        var gymBand = form.querySelector('#gym_band');
        var wantsGymNo = form.querySelector('input[name="wants_gym"][value="no"]');
        var wantsGymYes = form.querySelector('input[name="wants_gym"][value="yes"]');
        if (!gymBand || !wantsGymNo || !wantsGymYes) return;

        function updateRequired() {
            var addonsOnly = wantsGymNo.checked;
            gymBand.required = !addonsOnly;
            gymBand.setAttribute('aria-required', addonsOnly ? 'false' : 'true');
        }

        wantsGymNo.addEventListener('change', updateRequired);
        wantsGymYes.addEventListener('change', updateRequired);
        updateRequired();
    }

    ready(function () {
        initFlashDismiss();
        initSubmitLoading();
        initSignupValidation();
        initPreferencesGymBand();
    });
})();
