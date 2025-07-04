# Helm-чарт для установки приложения в Kubernetes

После успешной аутентификации в кластере склонируйте репозиторий этого чарта к себе на компьютер.

В файле `app/values.yaml` измените значения переменных. Укажите ссылку на реджистри, созданного в Yandex Cloud и версию образа:

```yaml
image:
  repository: "адрес образа в формате cr.yandex/<registry id>/<repo name>"
  pullPolicy: IfNotPresent
  # Overrides the image tag whose default is the chart appVersion.
  tag: "версия образа в реджистри"
```

Установите Helm-чарт:

```shell
helm upgrade --install --atomic test app
```

## Настройка реджистри Yandex Cloud

Для разрешения возможности пуллинга образов из вашего реджисти, настройте политику доступа. Нужно выдать роль `container-registry.images.puller` на ваш реестр для системной группы allUsers.

В настройках реджистри нажмите "Назначить роли" в правом верхнем углу и выберите группу "All Users":

<img src="img/regisry_all_users.png" alt="Contact Point" width="512"/>

Назначте этой группе роль `container-registry.images.puller`:

<img src="img/regisry_role.png" alt="Contact Point" width="512"/>


Ссылки на реджистри:

cr.yandex/crpn754eb9j71qae1kou/stg_service:v2025-06-09-r2

cr.yandex/crpn754eb9j71qae1kou/dds_service:v2025-06-10-r1

cr.yandex/crpn754eb9j71qae1kou/cdm_service:v2025-06-10-r1

![image](https://github.com/user-attachments/assets/0d46b2c8-7349-4455-8039-66813458beb2)
