import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[a-z]', password):
            raise ValidationError(_('رمز عبور باید حداقل یک حرف کوچک داشته باشد.'))
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_('رمز عبور باید حداقل یک حرف بزرگ داشته باشد.'))
        if not re.search(r'\d', password):
            raise ValidationError(_('رمز عبور باید حداقل یک عدد داشته باشد.'))
        if not re.search(r'[^A-Za-z0-9]', password):
            raise ValidationError(_('رمز عبور باید حداقل یک کاراکتر ویژه داشته باشد.'))

    def get_help_text(self):
        return _('رمز عبور باید شامل حداقل یک حرف کوچک، یک حرف بزرگ، یک عدد و یک کاراکتر ویژه باشد.')
