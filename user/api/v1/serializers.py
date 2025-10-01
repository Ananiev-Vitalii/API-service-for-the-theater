from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


User = get_user_model()


class UserMeSerializer(serializers.ModelSerializer):

    current_password = serializers.CharField(
        write_only=True,
        required=False,
        trim_whitespace=False,
        style={
            "input_type": "password",
            "placeholder": "Required when changing email or password",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=False,
        trim_whitespace=False,
        style={
            "input_type": "password",
            "placeholder": "New password. Requires current_password",
        },
    )

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
            "is_staff",
            "current_password",
            "password",
        )
        read_only_fields = ("id", "date_joined", "last_login", "is_staff")

    def validate_email(self, value: str) -> str:
        value = User.objects.normalize_email(value)
        instance = getattr(self, "instance", None)

        if value and instance and value != instance.email:
            if User.objects.filter(email=value).exclude(pk=instance.pk).exists():
                raise serializers.ValidationError("This email is already taken.")
        return value

    def validate_password(self, value: str) -> str:
        validate_password(value, user=self.instance)
        return value

    def validate(self, attrs: dict) -> dict:
        instance: User = self.instance
        want_change_email = "email" in attrs and attrs["email"] != instance.email
        want_change_password = "password" in attrs and attrs["password"]

        if want_change_email or want_change_password:
            current = attrs.get("current_password")
            if not current:
                raise serializers.ValidationError(
                    {"current_password": "Current password is required."}
                )
            if not instance.check_password(current):
                raise serializers.ValidationError(
                    {"current_password": "Current password is incorrect."}
                )

        return attrs

    def update(self, instance: User, validated_data: dict) -> User:
        validated_data.pop("current_password", None)
        new_password = validated_data.pop("password", None)

        for field in ("first_name", "last_name", "email"):
            if field in validated_data:
                setattr(instance, field, validated_data[field])

        if new_password:
            instance.set_password(new_password)

        instance.save(
            update_fields=(
                ["first_name", "last_name", "email", "password"]
                if new_password
                else ["first_name", "last_name", "email"]
            )
        )
        return instance


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password"},
    )
    password2 = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        style={"input_type": "password", "placeholder": "Repeat the password"},
    )

    class Meta:
        model = User
        fields = ("id", "email", "password", "password2", "first_name", "last_name")
        read_only_fields = ("id",)

    @staticmethod
    def validate_email(value: str) -> str:
        value = User.objects.normalize_email(value)

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already taken.")
        return value

    def validate(self, attrs: dict) -> dict:
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data: dict) -> User:
        validated_data.pop("password2", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
