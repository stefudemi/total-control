import re

from django.db import models


def normalize_phone(value: str) -> str:
    """Deja solo dígitos y un '+' inicial opcional."""
    value = (value or '').strip()
    digits = re.sub(r'\D', '', value)
    return f'+{digits}' if value.startswith('+') else digits


class Client(models.Model):
    """Cliente del complejo (quien reserva)."""

    first_name = models.CharField('nombre', max_length=100)
    last_name = models.CharField('apellido', max_length=100)
    phone = models.CharField('teléfono', max_length=20, unique=True)
    email = models.EmailField('email', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'cliente'
        verbose_name_plural = 'clientes'

    def save(self, *args, **kwargs):
        self.phone = normalize_phone(self.phone)
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def __str__(self):
        return f'{self.full_name} ({self.phone})'
