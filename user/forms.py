from crispy_forms.layout import HTML, Layout, Field, Submit
from crispy_forms.helper import FormHelper
from captcha.fields import CaptchaField
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

from user.models import CustomUser


class UserAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "base-form"
        self.helper.html5_required = True
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-control", "placeholder": f"{field.label}"}
            )

        self.helper.layout = Layout(
            HTML(
                """
                {% if form.errors %}
                    <p class="error-message">Invalid email address or password. Please try again.</p>
                {% endif %}
                """
            ),
            Field("username"),
            Field("password", template="forms/fields/password_toggle.html"),
            Submit(
                "submit",
                "Log in",
                css_class="btn btn-primary text-white btn-lg w-100 mt-4",
            ),
        )


class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "base-form"
        self.helper.html5_required = True
        self.helper.form_show_labels = False

        self.helper.layout = Layout(
            Field("email", placeholder="Email address", css_class="form-control"),
            Submit(
                "submit",
                "Send an email",
                css_class="btn btn-primary text-white btn-lg w-100 mt-4",
            ),
        )


class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "base-form"
        self.helper.html5_required = True
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False
        self.fields["new_password1"].help_text = ""
        self.fields["new_password2"].help_text = ""

        for field_name, field in self.fields.items():
            field.widget.attrs.update(
                {"class": "form-control", "placeholder": f"{field.label}"}
            )
        self.helper.layout = Layout(
            HTML(
                """
                {% if form.errors %}
                    {% for field, errors in form.errors.items %}
                        {% for error in errors %}
                            <p class="error-message">{{ error }}</p>
                        {% endfor %}
                    {% endfor %}
                {% endif %}
                """
            ),
            Field("new_password1", template="forms/fields/password_toggle.html"),
            Field("new_password2", template="forms/fields/password_toggle.html"),
            Submit(
                "submit",
                "Change Password",
                css_class="btn btn-primary text-white btn-lg w-100 mt-4",
            ),
        )


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "password1",
            "password2",
        ]

    captcha = CaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.form_class = "base-form"
        self.helper.html5_required = True
        self.helper.form_show_labels = False
        self.helper.form_show_errors = False
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

        for field_name, field in self.fields.items():
            if field_name != "captcha":
                field.widget.attrs.update(
                    {
                        "class": "form-control",
                        "required": "required",
                        "placeholder": f"{field.label}",
                    }
                )
            else:
                field.widget.attrs.update({"placeholder": "Enter text from the image"})

        self.helper.layout = Layout(
            HTML(
                """
                {% if form.errors %}
                    {% for field, errors in form.errors.items %}
                        {% for error in errors %}
                            <p class="error-message">{{ error }}</p>
                        {% endfor %}
                    {% endfor %}
                {% endif %}
                """
            ),
            Field("email"),
            Field("first_name"),
            Field("last_name"),
            Field("password1", template="forms/fields/password_toggle.html"),
            Field("password2", template="forms/fields/password_toggle.html"),
            Field("captcha"),
            Submit(
                "submit",
                "Register",
                css_class="btn btn-primary text-white btn-lg w-100 mt-4",
            ),
        )
