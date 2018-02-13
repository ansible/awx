let Base;

function NotificationTemplateModel (method, resource, config) {
    Base.call(this, 'notification_templates');

    this.Constructor = NotificationTemplateModel;

    return this.create(method, resource, config);
}

function NotificationTemplateModelLoader (BaseModel) {
    Base = BaseModel;

    return NotificationTemplateModel;
}

NotificationTemplateModelLoader.$inject = [
    'BaseModel'
];

export default NotificationTemplateModelLoader;
