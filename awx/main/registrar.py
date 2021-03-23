# Copyright (c) 2015 Ansible, Inc.
# All Rights Reserved.

from django.db.models.signals import pre_save, post_save, pre_delete, m2m_changed


class ActivityStreamRegistrar(object):
    def __init__(self):
        self.models = []

    def connect(self, model):
        # Always register model; the signal handlers will check if activity stream is enabled.
        from awx.main.signals import activity_stream_create, activity_stream_update, activity_stream_delete, activity_stream_associate

        if model not in self.models:
            self.models.append(model)
            post_save.connect(activity_stream_create, sender=model, dispatch_uid=str(self.__class__) + str(model) + "_create")
            pre_save.connect(activity_stream_update, sender=model, dispatch_uid=str(self.__class__) + str(model) + "_update")
            pre_delete.connect(activity_stream_delete, sender=model, dispatch_uid=str(self.__class__) + str(model) + "_delete")

            for m2mfield in model._meta.many_to_many:
                try:
                    m2m_attr = getattr(model, m2mfield.name)
                    m2m_changed.connect(
                        activity_stream_associate, sender=m2m_attr.through, dispatch_uid=str(self.__class__) + str(m2m_attr.through) + "_associate"
                    )
                except AttributeError:
                    pass

    def disconnect(self, model):
        if model in self.models:
            post_save.disconnect(dispatch_uid=str(self.__class__) + str(model) + "_create")
            pre_save.disconnect(dispatch_uid=str(self.__class__) + str(model) + "_update")
            pre_delete.disconnect(dispatch_uid=str(self.__class__) + str(model) + "_delete")
            self.models.pop(model)

            for m2mfield in model._meta.many_to_many:
                m2m_attr = getattr(model, m2mfield.name)
                m2m_changed.disconnect(dispatch_uid=str(self.__class__) + str(m2m_attr.through) + "_associate")


activity_stream_registrar = ActivityStreamRegistrar()
