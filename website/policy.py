from password_strength import PasswordPolicy

policy = PasswordPolicy.from_names(
    length=8,
    uppercase=1,
    numbers=1,
    strength=0.1
)