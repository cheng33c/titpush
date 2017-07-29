from django.db import models

# Create your models here.
class PeopleModel(models.Model):
    phone = models.CharField('手机', max_length=11)
    email = models.CharField('邮箱', max_length=255)

    class Meta:
        verbose_name = '使用者信息'
        verbose_name_plural = '使用者信息'
