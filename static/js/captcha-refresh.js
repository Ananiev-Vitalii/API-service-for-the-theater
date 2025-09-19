document.addEventListener('DOMContentLoaded', function() {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    const csrftoken = getCookie('csrftoken');

    const captchaImages = document.querySelectorAll('img.captcha');
    captchaImages.forEach(function(img) {
        img.style.cursor = 'pointer';
        img.addEventListener('click', function() {
            $.ajax({
                url: '/captcha/refresh/',
                type: 'POST',
                dataType: 'json',
                data: {},
                headers: {
                    'X-CSRFToken': csrftoken
                },
                success: function(data) {
                    if (data && data.image_url && data.key) {
                        img.src = data.image_url;
                        const hiddenInput = document.getElementById('id_captcha_0');
                        if (hiddenInput) {
                            hiddenInput.value = data.key;
                        }
                        const captchaInput = document.getElementById('id_captcha_1');
                        if (captchaInput) {
                            captchaInput.value = '';
                        }
                    }
                },
                error: function(xhr, errmsg, err) {
                    console.log("Error during update CAPTCHA: ", errmsg);
                }
            });
        });
    });
});