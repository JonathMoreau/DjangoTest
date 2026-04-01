import secrets

from django.contrib.auth.hashers import check_password, make_password
from django.db import models
from django.utils import timezone


class ApiClient(models.Model):
    name = models.CharField(max_length=150, unique=True)
    client_id = models.CharField(max_length=24, unique=True, editable=False)
    description = models.TextField(blank=True)
    scopes = models.JSONField(default=list, blank=True)
    secret_prefix = models.CharField(max_length=12, blank=True, editable=False)
    secret_hash = models.CharField(max_length=128, blank=True, editable=False)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = secrets.token_hex(6)
        super().save(*args, **kwargs)

    def has_scopes(self, required_scopes):
        return set(required_scopes).issubset(set(self.scopes))

    def check_secret(self, raw_secret):
        if not self.secret_hash:
            return False
        return check_password(raw_secret, self.secret_hash)

    def rotate_secret(self):
        raw_secret = secrets.token_urlsafe(24)
        self.secret_prefix = raw_secret[:8]
        self.secret_hash = make_password(raw_secret)
        if not self.client_id:
            self.client_id = secrets.token_hex(6)
        self.save()
        return f"{self.client_id}.{raw_secret}"

    def mark_used(self):
        self.last_used_at = timezone.now()
        self.save(update_fields=["last_used_at"])
